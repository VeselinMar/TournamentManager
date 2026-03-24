from django.db import models
from tournamentapp.models import Tournament


class SideEvent(models.Model):
    tournament = models.ForeignKey(
        Tournament,
        on_delete=models.CASCADE,
        related_name='side_events'
    )
    name = models.CharField(
        max_length=200,
        )
    description = models.TextField(
        blank=True,
        )
    start_time = models.DateTimeField(
        blank=True, 
        null=True,
        )
    end_time = models.DateTimeField(
        blank=True, 
        null=True,
        )
    is_active = models.BooleanField(
        default=True,
        )

    class Meta:
        ordering = ['start_time']

    def __str__(self):
        return f"{self.name} ({self.tournament.name})"