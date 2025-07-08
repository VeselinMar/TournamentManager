from django.urls import path
from .views import HomePageView, TeamCreateView, MatchCreateView, MatchDetailView, MatchEditView, LeaderboardView, TeamListView, TeamDetailView

urlpatterns = [
    path('', HomePageView.as_view(), name='home'),
    path('teams/', TeamListView.as_view(), name='team-list'),
    path('teams/<int:pk>/', TeamDetailView.as_view(), name='team-detail'),
    path('teams/create/', TeamCreateView.as_view(), name='team-create'),
    path('matches/create/', MatchCreateView.as_view(), name='match-create'),
    path('matches/<int:pk>/', MatchDetailView.as_view(), name='match-detail'),
    path('matches/<int:pk>/edit/', MatchEditView.as_view(), name='match-edit'),
    path('leaderboard/', LeaderboardView.as_view(), name='leaderboard'),
]
