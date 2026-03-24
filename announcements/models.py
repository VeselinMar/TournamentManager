from django.db import models
from django.utils import timezone
from tournamentapp.models import Tournament


class Announcement(models.Model):
    tournament = models.ForeignKey(
        Tournament,
        on_delete=models.CASCADE,
        related_name='announcements'
    )
    message = models.TextField()
    starts_at = models.DateTimeField()
    ends_at = models.DateTimeField()
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Announcement ({self.tournament.name}) — {self.starts_at}"

    @property
    def is_currently_active(self):
        now = timezone.now()
        return self.is_active and self.starts_at <= now <= self.ends_at