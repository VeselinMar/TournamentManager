from django.urls import path
from .views import SideEventListView, SideEventCreateView, SideEventUpdateView, SideEventDeleteView

urlpatterns = [
    path('tournament/<int:tournament_id>/programme/', SideEventListView.as_view(), name='sideevent-list'),
    path('tournament/<int:tournament_id>/programme/create/', SideEventCreateView.as_view(), name='sideevent-create'),
    path('tournament/<int:tournament_id>/programme/<int:pk>/edit/', SideEventUpdateView.as_view(), name='sideevent-edit'),
    path('tournament/<int:tournament_id>/programme/<int:pk>/delete/', SideEventDeleteView.as_view(), name='sideevent-delete'),
]