from django.urls import path
from .views import HomePageView, TeamCreateView, MatchCreateView

urlpatterns = [
    path('', HomePageView.as_view(), name='home'),
    path('teams/create/', TeamCreateView.as_view(), name='team-create'),
    path('matches/create/', MatchCreateView.as_view(), name='match-create'),
]
