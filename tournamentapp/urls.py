from django.urls import path
from .views import (
    TournamentCreateView, TournamentPublicView, TournamentDetailView, LandingPageView,
    TeamListView, TeamDetailView, TeamCreateView,
    MatchCreateView, MatchDetailView, MatchEditView, LeaderboardView, FieldAddView,
    create_match_event, add_player, finish_match, remove_match_event, field_edit, field_delete,
    generate_tournament_schedule
)
urlpatterns = [
    path('', LandingPageView.as_view(), name='landing-page'),

    # Tournament general
    path('tournament/create/', TournamentCreateView.as_view(), name='tournament-create'),
    path('tournament/<int:pk>/', TournamentDetailView.as_view(), name='tournament-detail'),
    path('public/<slug:slug>/', TournamentPublicView.as_view(), name='public-tournament-leaderboard'),
    path('tournament/<int:tournament_id>/generate-schedule/', generate_tournament_schedule, name='generate-tournament-schedule'),

    # Teams (tournament-specific)
    path('tournament/<int:tournament_id>/teams/', TeamListView.as_view(), name='team-list'),
    path('tournament/<int:tournament_id>/teams/<int:pk>/', TeamDetailView.as_view(), name='team-detail'),
    path('tournament/<int:tournament_id>/teams/create/', TeamCreateView.as_view(), name='team-create'),
    path('tournament/<int:tournament_id>/teams/<int:team_id>/add-player/', add_player, name='add-player'),

    # Matches (tournament-specific)
    path('tournament/<int:tournament_id>/matches/create/', MatchCreateView.as_view(), name='match-create'),
    path('tournament/<int:tournament_id>/matches/<int:pk>/', MatchDetailView.as_view(), name='match-detail'),
    path('tournament/<int:tournament_id>/matches/<int:pk>/edit/', MatchEditView.as_view(), name='match-edit'),
    path('tournament/<int:tournament_id>/matches/<int:match_id>/add-event/', create_match_event, name='add-match-event'),
    path('tournament/<int:tournament_id>/matches/<int:match_id>/finish/', finish_match, name='finish-match'),
    path('tournament/<int:tournament_id>/matches/delete-event/<int:event_id>/', remove_match_event, name='delete-match-event'),

    # Fields (tournament-specific)
    path('tournament/<int:tournament_id>/fields/create/', FieldAddView.as_view(), name='field-create'),
    path('tournament/<int:tournament_id>/fields/<int:pk>/edit/', field_edit, name='edit-field'),
    path('tournament/<int:tournament_id>/fields/<int:pk>/delete/', field_delete, name='delete-field'),

    # Leaderboard (tournament-specific)
    path('tournament/<int:tournament_id>/leaderboard/', LeaderboardView.as_view(), name='leaderboard'),
]