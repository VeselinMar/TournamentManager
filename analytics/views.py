import csv

from django.contrib.auth.decorators import login_required
from django.http import Http404, HttpResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404, render
from django.utils.text import slugify
from django.views.decorators.cache import never_cache
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle
from rest_framework.views import APIView

from sponsors.models import SponsorBanner
from tournamentapp.models import Tournament

from .models import SponsorDailyStats
from .services import (
    SECTIONS, click_rate, is_probably_human, record_page_view, record_sponsor_click, tournament_report,
)


class TrackViewAPIView(APIView):
    """
    Beacon sent by the public page once per section view.
    No authentication (so no CSRF for logged-in organisers) and nothing
    personal is stored; the rate limit only keeps the IP in memory briefly.
    """
    authentication_classes = []
    permission_classes = [AllowAny]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "tracking"

    def post(self, request, slug):
        tournament = get_object_or_404(Tournament, slug=slug)
        section = request.data.get("section") if hasattr(request.data, "get") else None
        if section not in SECTIONS:
            return Response({"detail": "Unknown section."}, status=status.HTTP_400_BAD_REQUEST)

        if is_probably_human(request):
            record_page_view(tournament, section)
        return Response(status=status.HTTP_204_NO_CONTENT)


@never_cache
def sponsor_click(request, pk):
    """Count a click on a sponsor logo, then send the visitor to the sponsor's site."""
    sponsor = get_object_or_404(SponsorBanner, pk=pk)
    if not sponsor.link_url:
        raise Http404("This sponsor has no website.")
    if is_probably_human(request):
        record_sponsor_click(sponsor)
    response = HttpResponseRedirect(sponsor.link_url)
    response["X-Robots-Tag"] = "noindex, nofollow"
    return response


@login_required
def tournament_stats(request, tournament_id):
    tournament = get_object_or_404(Tournament, pk=tournament_id, owner=request.user)
    return render(request, "analytics/stats.html", {
        "tournament": tournament,
        "report": tournament_report(tournament),
    })


@login_required
def sponsor_stats_csv(request, tournament_id):
    """Per sponsor and day — ready to send to sponsors."""
    tournament = get_object_or_404(Tournament, pk=tournament_id, owner=request.user)
    rows = (
        SponsorDailyStats.objects.filter(sponsor__tournament=tournament)
        .select_related("sponsor")
        .order_by("sponsor__name", "date")
    )

    response = HttpResponse(content_type="text/csv; charset=utf-8")
    filename = f"{slugify(tournament.name) or 'tournament'}-sponsor-stats.csv"
    response["Content-Disposition"] = f'attachment; filename="{filename}"'
    response.write("﻿")  # BOM so Excel opens UTF-8 (Cyrillic names) correctly

    writer = csv.writer(response)
    writer.writerow(["Date", "Sponsor", "Logo shown (page views)", "Clicks", "Click rate %"])
    for row in rows:
        writer.writerow([
            row.date.isoformat(), row.sponsor.name, row.impressions, row.clicks,
            click_rate(row.clicks, row.impressions),
        ])
    return response
