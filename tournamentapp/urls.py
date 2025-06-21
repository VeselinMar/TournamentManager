from django.urls import path
from .views import HomePageView, TeamCreateView, MatchCreateView, MatchDetailView, MatchEditView, TopScorersView

urlpatterns = [
    path('', HomePageView.as_view(), name='home'),
    path('teams/create/', TeamCreateView.as_view(), name='team-create'),
    path('matches/create/', MatchCreateView.as_view(), name='match-create'),
    path('matches/<int:pk>/', MatchDetailView.as_view(), name='match-detail'),
    path('matches/<int:pk>/edit/', MatchEditView.as_view(), name='match-edit'),
    path('leaderboard/scorers/', TopScorersView.as_view(), name='top-scorers'),
]
