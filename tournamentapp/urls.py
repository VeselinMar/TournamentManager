from django.urls import path
from .views import (
    HomePageView, TeamListView, TeamDetailView, TeamCreateView,
    MatchCreateView, MatchDetailView, MatchEditView, LeaderboardView, create_match_event, add_player, finish_match
)
urlpatterns = [
    path('', HomePageView.as_view(), name='home'),
    path('teams/', TeamListView.as_view(), name='team-list'),
    path('teams/<int:pk>/', TeamDetailView.as_view(), name='team-detail'),
    path('teams/create/', TeamCreateView.as_view(), name='team-create'),
    path('matches/create/', MatchCreateView.as_view(), name='match-create'),
    path('matches/<int:pk>/', MatchDetailView.as_view(), name='match-detail'),
    path('matches/<int:pk>/edit/', MatchEditView.as_view(), name='match-edit'),
    path('matches/<int:match_id>/add-event/', create_match_event, name='create-match-event'),
    path('leaderboard/', LeaderboardView.as_view(), name='leaderboard'),
    path('teams/<str:team_name>/add-player/', add_player, name='add-player'),
    path('matches/<int:match_id>/finish/', finish_match, name='finish-match'),
]
