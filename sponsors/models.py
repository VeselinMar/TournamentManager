from django.db import models
from tournamentapp.models import Tournament

class SponsorBanner(models.Model):
    tournament = models.ForeignKey(
        "tournamentapp.Tournament", 
        on_delete=models.CASCADE, 
        related_name="sponsors"
    )
    name = models.CharField(
        max_length=100,
        help_text="Internal name for the banner"
    )
    link_url = models.URLField(
        blank=True,
        null=True,
        help_text="Optional link to sponsor website"
    )
    image = models.ImageField(
        upload_to="sponsors/",
        help_text="Upload sponsor banner image"
    )
    uploaded_at = models.DateTimeField(
        auto_now_add = True
    )
    
    class Meta:
        ordering = ["uploaded_at"]

    def __str__(self):
        return f"{self.name} ({self.tournament.name})"