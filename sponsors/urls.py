from django.urls import path
from .views import SponsorBannerCreateView, SponsorBannerListView

urlpatterns = [
    path('tournament/<int:tournament_id>/banners/', SponsorBannerListView.as_view(), name='sponsor-list'),
    path('tournament/<int:tournament_id>/banners/add/', SponsorBannerCreateView.as_view(), name='sponsor-add'),
]