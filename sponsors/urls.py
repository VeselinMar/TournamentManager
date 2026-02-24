from django.urls import path
from .views import SponsorBannerCreateView, SponsorBannerListView, delete_sponsor_banner

urlpatterns = [
    path('tournament/<int:tournament_id>/banners/', SponsorBannerListView.as_view(), name='sponsor-list'),
    path('tournament/<int:tournament_id>/banners/add/', SponsorBannerCreateView.as_view(), name='sponsor-add'),
    path('tournament/<int:tournament_id>/banners/delete-banner/<int:pk>', delete_sponsor_banner, name='sponsor-remove')
]