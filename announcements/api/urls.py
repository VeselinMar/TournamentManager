from django.urls import path
from .views import AnnouncementsListAPIView

urlpatterns = [
    path('tournaments/<slug:slug>/announcements/', AnnouncementsListAPIView.as_view(), name='api-announcements'),
]