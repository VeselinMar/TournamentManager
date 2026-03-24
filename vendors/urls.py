from django.urls import path
from .views import VendorListView, VendorCreateView, VendorUpdateView, VendorDeleteView

urlpatterns = [
    path('tournament/<int:tournament_id>/vendors/', VendorListView.as_view(), name='vendor-list'),
    path('tournament/<int:tournament_id>/vendors/create/', VendorCreateView.as_view(), name='vendor-create'),
    path('tournament/<int:tournament_id>/vendors/<int:pk>/edit/', VendorUpdateView.as_view(), name='vendor-edit'),
    path('tournament/<int:tournament_id>/vendors/<int:pk>/delete/', VendorDeleteView.as_view(), name='vendor-delete'),
]