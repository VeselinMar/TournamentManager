from django.urls import path
from .views import HomePageView, TeamCreateView

urlpatterns = [
    path('', HomePageView.as_view(), name='home'),
    path('teams/create/', TeamCreateView.as_view(), name='team-create'),
]
