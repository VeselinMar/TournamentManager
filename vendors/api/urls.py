from django.urls import path
from .views import VendorListAPIView

urlpatterns = [
    path('tournaments/<slug:slug>/vendors/', VendorListAPIView.as_view(), name='api-vendors'),
]