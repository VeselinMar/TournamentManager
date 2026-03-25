from django.urls import path
from .views import ScheduleAPIView, LeaderboardAPIView

urlpatterns = [
    path('tournaments/<slug:slug>/schedule/', ScheduleAPIView.as_view(), name='api-schedule'),
    path('tournaments/<slug:slug>/leaderboard/', LeaderboardAPIView.as_view(), name='api-leaderboard'),
]