from django.urls import path
from .views import (
    AnnouncementListView, AnnouncementCreateView,
    AnnouncementUpdateView, AnnouncementDeleteView
)

urlpatterns = [
    path('tournament/<int:tournament_id>/announcements/', AnnouncementListView.as_view(), name='announcement-list'),
    path('tournament/<int:tournament_id>/announcements/create/', AnnouncementCreateView.as_view(), name='announcement-create'),
    path('tournament/<int:tournament_id>/announcements/<int:pk>/edit/', AnnouncementUpdateView.as_view(), name='announcement-edit'),
    path('tournament/<int:tournament_id>/announcements/<int:pk>/delete/', AnnouncementDeleteView.as_view(), name='announcement-delete'),
]