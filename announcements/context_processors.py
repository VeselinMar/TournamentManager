from django.utils import timezone
from .models import Announcement


def active_announcements(request):
    tournament_id = request.resolver_match.kwargs.get('tournament_id') or \
                    request.resolver_match.kwargs.get('pk')
    if not tournament_id:
        return {}
    now = timezone.now()
    announcements = Announcement.objects.filter(
        tournament_id=tournament_id,
        is_active=True,
        starts_at__lte=now,
        ends_at__gte=now
    )
    return {'active_announcements': announcements}