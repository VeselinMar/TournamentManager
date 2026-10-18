from django.urls import path

from .views import TrackViewAPIView, sponsor_click, sponsor_stats_csv, tournament_stats

urlpatterns = [
    path("api/tournaments/<slug:slug>/track/", TrackViewAPIView.as_view(), name="api-track-view"),
    path("go/sponsor/<int:pk>/", sponsor_click, name="sponsor-click"),
    path("tournament/<int:tournament_id>/stats/", tournament_stats, name="tournament-stats"),
    path("tournament/<int:tournament_id>/stats/sponsors.csv", sponsor_stats_csv, name="tournament-stats-csv"),
]
