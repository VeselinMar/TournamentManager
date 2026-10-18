from django.contrib import admin

# Register your models here.
from django.contrib import admin
from .models import Team, Player, Match, GoalEvent, Field, MatchEvent, Tournament, Group, MatchSlot

@admin.register(Tournament)
class TournamentAdmin(admin.ModelAdmin):
    list_display = ('name', 'owner', 'slug')
    search_fields = ('owner__email', 'name')

@admin.register(Team)
class TeamAdmin(admin.ModelAdmin):
    list_display = ('name', 'group', 'tournament')
    list_filter = ('tournament',)
    search_fields = ('name',)

@admin.register(Player)
class PlayerAdmin(admin.ModelAdmin):
    list_display = ('name', 'team',)
    list_filter = ('team',)
    search_fields = ('name',)

@admin.register(Match)
class MatchAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'stage', 'round', 'start_time', 'field', 'home_score', 'away_score', 'is_finished')
    list_filter = ('stage', 'is_finished', 'tournament')
    search_fields = ('home_team__name', 'away_team__name')
    ordering = ('start_time',)

@admin.register(GoalEvent)
class GoalAdmin(admin.ModelAdmin):
    list_display = ('match', 'player', 'team')
    search_fields = ('player__name', 'team__name')

@admin.register(Field)
class FieldAdmin(admin.ModelAdmin):
    list_display = ('name', 'tournament')
    search_fields = ('name', 'tournament__name')

@admin.register(MatchEvent)
class MatchEventAdmin(admin.ModelAdmin):
    list_display = ('match', 'event_type', 'player', 'team', 'minute')
    list_filter = ('event_type', 'team')
    search_fields = ('player__name', 'team__name')
    ordering = ('match', 'minute')

@admin.register(Group)
class GroupAdmin(admin.ModelAdmin):
    list_display = ('name', 'tournament', 'order')
    list_filter = ('tournament',)


@admin.register(MatchSlot)
class MatchSlotAdmin(admin.ModelAdmin):
    list_display = ('match', 'side', 'source_type', 'seed', 'source_match', 'placeholder', 'is_manual_override')
    list_filter = ('source_type', 'is_manual_override')
