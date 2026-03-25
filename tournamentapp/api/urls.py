from django.urls import path
from .views import ScheduleAPIView, LeaderboardAPIView, TournamentMetaAPIView

urlpatterns = [
    path('tournaments/<slug:slug>/', TournamentMetaAPIView.as_view(), name='api-tournament-meta'),
    path('tournaments/<slug:slug>/schedule/', ScheduleAPIView.as_view(), name='api-schedule'),
    path('tournaments/<slug:slug>/leaderboard/', LeaderboardAPIView.as_view(), name='api-leaderboard'),
]