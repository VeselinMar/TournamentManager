from django.urls import path
from .views import SideEventListAPIView

urlpatterns = [
    path('tournaments/<slug:slug>/side-events/', SideEventListAPIView.as_view(), name='api-side-events'),
]