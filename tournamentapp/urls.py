from django.urls import path
from .views import (
    HomePageView, TeamListView, TeamDetailView, TeamCreateView,
    MatchCreateView, MatchDetailView, MatchEditView, LeaderboardView, FieldAddView,
    create_match_event, add_player, finish_match, remove_match_event, field_edit, field_delete
)
urlpatterns = [
    path('', HomePageView.as_view(), name='home'),
    path('teams/', TeamListView.as_view(), name='team-list'),
    path('teams/<int:pk>/', TeamDetailView.as_view(), name='team-detail'),
    path('teams/create/', TeamCreateView.as_view(), name='team-create'),
    path('matches/create/', MatchCreateView.as_view(), name='match-create'),
    path('matches/<int:pk>/', MatchDetailView.as_view(), name='match-detail'),
    path('matches/<int:pk>/edit/', MatchEditView.as_view(), name='match-edit'),
    path('matches/<int:match_id>/add-event/', create_match_event, name='add-match-event'),
    path('leaderboard/', LeaderboardView.as_view(), name='leaderboard'),
    path('teams/<int:team_id>/add-player/', add_player, name='add-player'),
    path('matches/<int:match_id>/finish/', finish_match, name='finish-match'),
    path('fields/create/', FieldAddView.as_view(), name='field-create'),
    path('fields/<int:pk>/edit/', field_edit, name='edit-field'),
    path('fields/<int:pk>/delete/', field_delete, name='delete-field'),
    path('matches/delete-event/<int:event_id>/', remove_match_event, name='delete-match-event'),
]
