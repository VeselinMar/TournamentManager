from django.db import models
from tournamentapp.models import Tournament


class Vendor(models.Model):
    tournament = models.ForeignKey(
        Tournament,
        on_delete=models.CASCADE,
        related_name='vendors'
    )
    name = models.CharField(
        max_length=100,
        )
    description = models.TextField(
        blank=True,
        )
    category = models.CharField(
        max_length=100, 
        blank=True,
        )
    image = models.ImageField(
        upload_to='vendors/', 
        blank=True, 
        null=True,
        )
    is_active = models.BooleanField(
        default=True,
        )

    class Meta:
        ordering = ['name']

    def __str__(self):
        return f"{self.name} ({self.tournament.name})"