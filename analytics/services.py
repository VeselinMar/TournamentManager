"""Counter updates and report queries."""
import re
from dataclasses import dataclass

from django.db.models import F, Sum
from django.utils import timezone

from sponsors.models import SponsorBanner

from .models import PageViewCount, SponsorDailyStats

SECTIONS = {choice for choice, _ in PageViewCount.SECTION_CHOICES}

# Crawlers, link previews and scripts are not visitors
_NON_HUMAN = re.compile(
    r"bot|crawl|spider|slurp|preview|facebookexternalhit|whatsapp|telegram|"
    r"headless|lighthouse|python-requests|curl|wget|httpclient",
    re.IGNORECASE,
)


def is_probably_human(request):
    agent = request.META.get("HTTP_USER_AGENT", "")
    return bool(agent) and not _NON_HUMAN.search(agent)


def record_page_view(tournament, section, date=None):
    """One section view: counts the view and an impression for every sponsor on the page."""
    date = date or timezone.localdate()

    PageViewCount.objects.bulk_create(
        [PageViewCount(tournament=tournament, date=date, section=section)],
        ignore_conflicts=True,
    )
    PageViewCount.objects.filter(tournament=tournament, date=date, section=section).update(views=F("views") + 1)

    sponsor_ids = list(tournament.sponsors.values_list("pk", flat=True))
    if sponsor_ids:
        SponsorDailyStats.objects.bulk_create(
            [SponsorDailyStats(sponsor_id=pk, date=date) for pk in sponsor_ids],
            ignore_conflicts=True,
        )
        SponsorDailyStats.objects.filter(sponsor_id__in=sponsor_ids, date=date).update(
            impressions=F("impressions") + 1
        )


def record_sponsor_click(sponsor, date=None):
    date = date or timezone.localdate()
    SponsorDailyStats.objects.bulk_create([SponsorDailyStats(sponsor=sponsor, date=date)], ignore_conflicts=True)
    SponsorDailyStats.objects.filter(sponsor=sponsor, date=date).update(clicks=F("clicks") + 1)


def click_rate(clicks, impressions):
    return round(100 * clicks / impressions, 1) if impressions else 0.0


@dataclass
class SponsorReportRow:
    sponsor: SponsorBanner
    impressions: int
    clicks: int

    @property
    def click_rate(self):
        return click_rate(self.clicks, self.impressions)


def tournament_report(tournament):
    views = PageViewCount.objects.filter(tournament=tournament)
    section_labels = dict(PageViewCount.SECTION_CHOICES)

    by_section = [
        {"section": section_labels.get(row["section"], row["section"]), "views": row["total"]}
        for row in views.values("section").annotate(total=Sum("views")).order_by("-total")
    ]
    by_day = list(views.values("date").annotate(total=Sum("views")).order_by("date"))

    sponsors = []
    for sponsor in tournament.sponsors.order_by("name"):
        totals = sponsor.daily_stats.aggregate(impressions=Sum("impressions"), clicks=Sum("clicks"))
        sponsors.append(SponsorReportRow(
            sponsor=sponsor,
            impressions=totals["impressions"] or 0,
            clicks=totals["clicks"] or 0,
        ))

    return {
        "total_views": sum(row["views"] for row in by_section),
        "by_section": by_section,
        "by_day": by_day,
        "sponsors": sponsors,
    }
