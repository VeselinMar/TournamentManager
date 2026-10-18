"""
Bump a tournament's cache version whenever data shown on its public page changes.

Covers saves and deletes made anywhere (views, forms, admin). Bulk database
operations that bypass signals (`bulk_create`, `QuerySet.update`) call
`cache.invalidate` explicitly where they are used.
"""
from django.db.models.signals import post_delete, post_save

from announcements.models import Announcement
from programme.models import SideEvent
from sponsors.models import SponsorBanner
from vendors.models import Vendor

from .cache import invalidate
from .models import Field, Group, Match, MatchEvent, MatchSlot, Player, Team, Tournament


def _match_tournament_id(match_id):
    return Match.objects.filter(pk=match_id).values_list('tournament_id', flat=True).first()


def _team_tournament_id(team_id):
    return Team.objects.filter(pk=team_id).values_list('tournament_id', flat=True).first()


def _tournament_id(instance):
    if isinstance(instance, Tournament):
        return instance.pk
    if isinstance(instance, Player):
        cached_team = instance._state.fields_cache.get('team')
        return cached_team.tournament_id if cached_team else _team_tournament_id(instance.team_id)
    if isinstance(instance, (MatchEvent, MatchSlot)):
        cached_match = instance._state.fields_cache.get('match')
        return cached_match.tournament_id if cached_match else _match_tournament_id(instance.match_id)
    return instance.tournament_id


# Analytics counters are deliberately NOT listed: page views must not
# invalidate the cache they are served from.
PUBLIC_MODELS = (
    Tournament, Group, Team, Player, Field, Match, MatchSlot, MatchEvent,
    SponsorBanner, Vendor, SideEvent, Announcement,
)


def _on_change(sender, instance, raw=False, **kwargs):
    if raw:  # fixtures / loaddata
        return
    invalidate(_tournament_id(instance))


for _model in PUBLIC_MODELS:
    post_save.connect(_on_change, sender=_model, dispatch_uid=f"cache-save-{_model.__name__}")
    post_delete.connect(_on_change, sender=_model, dispatch_uid=f"cache-delete-{_model.__name__}")
