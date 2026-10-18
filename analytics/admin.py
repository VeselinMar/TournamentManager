from django.contrib import admin

from .models import PageViewCount, SponsorDailyStats


@admin.register(PageViewCount)
class PageViewCountAdmin(admin.ModelAdmin):
    list_display = ("tournament", "date", "section", "views")
    list_filter = ("tournament", "section")


@admin.register(SponsorDailyStats)
class SponsorDailyStatsAdmin(admin.ModelAdmin):
    list_display = ("sponsor", "date", "impressions", "clicks")
    list_filter = ("sponsor__tournament",)
