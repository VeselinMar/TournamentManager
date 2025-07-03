from django.contrib import admin

# Register your models here.
from django.contrib import admin
from .models import Team, Player, Match, GoalEvent, Field, MatchEvent

@admin.register(Team)
class TeamAdmin(admin.ModelAdmin):
    list_display = ('name', 'tournament_points',)
    search_fields = ('name',)

@admin.register(Player)
class PlayerAdmin(admin.ModelAdmin):
    list_display = ('name', 'team', 'goals', 'yellow_cards', 'red_cards', 'is_allowed_to_play')
    list_filter = ('team', 'is_allowed_to_play')
    search_fields = ('name',)

@admin.register(Match)
class MatchAdmin(admin.ModelAdmin):
    list_display = ('home_team', 'away_team', 'start_time', 'field', 'home_score', 'away_score', 'is_finished')
    list_filter = ('field', 'is_finished')
    search_fields = ('home_team__name', 'away_team__name')
    ordering = ('start_time',)

@admin.register(GoalEvent)
class GoalAdmin(admin.ModelAdmin):
    list_display = ('match', 'player', 'team')
    search_fields = ('player__name', 'team__name')

@admin.register(Field)
class FieldAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)

@admin.register(MatchEvent)
class MatchEventAdmin(admin.ModelAdmin):
    list_display = ('match', 'event_type', 'player', 'team', 'minute')
    list_filter = ('event_type', 'team')
    search_fields = ('player__name', 'team__name')
    ordering = ('match', 'minute')