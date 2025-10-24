from django.contrib import admin
from .models import SponsorBanner

# Register your models here.
@admin.register(SponsorBanner)
class SponsorBannerAdmin(admin.ModelAdmin):
    list_display = ("name", "tournament", "uploaded_at")
    list_filter = ("tournament",)