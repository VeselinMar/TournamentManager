"""
Anonymous, aggregated statistics for the public tournament page.

Only daily totals are stored: no cookies, no IP addresses, no user IDs.
This keeps the counters outside GDPR consent requirements while giving
organisers numbers they can show to sponsors.
"""
from django.db import models

from sponsors.models import SponsorBanner
from tournamentapp.models import Tournament


class PageViewCount(models.Model):
    SECTION_CHOICES = [
        ("schedule", "Schedule"),
        ("leaderboard", "Leaderboard / Groups"),
        ("bracket", "Bracket"),
        ("vendors", "Vendors"),
        ("side-events", "Side events"),
    ]

    tournament = models.ForeignKey(Tournament, on_delete=models.CASCADE, related_name="page_view_counts")
    date = models.DateField()
    section = models.CharField(max_length=20, choices=SECTION_CHOICES)
    views = models.PositiveIntegerField(default=0)

    class Meta:
        unique_together = ("tournament", "date", "section")
        ordering = ["date", "section"]

    def __str__(self):
        return f"{self.tournament.name} {self.date} {self.section}: {self.views}"


class SponsorDailyStats(models.Model):
    sponsor = models.ForeignKey(SponsorBanner, on_delete=models.CASCADE, related_name="daily_stats")
    date = models.DateField()
    impressions = models.PositiveIntegerField(default=0, help_text="Page views on which the logo was shown.")
    clicks = models.PositiveIntegerField(default=0)

    class Meta:
        unique_together = ("sponsor", "date")
        ordering = ["date"]
        verbose_name_plural = "Sponsor daily stats"

    def __str__(self):
        return f"{self.sponsor.name} {self.date}: {self.impressions} shown / {self.clicks} clicks"
