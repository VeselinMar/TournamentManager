from django.db import models
from tournamentapp.models import Tournament
from django.core.files.base import ContentFile
from django.core.exceptions import ValidationError
from PIL import Image
from PIL import UnidentifiedImageError
from io import BytesIO
import os
import uuid


class SponsorBanner(models.Model):
    """
    Sponsor banner images are normalized on save:
    - resized to OUTPUT_MAX_* bounds
    - converted to WebP
    - uniquely named
    """
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
    # image Consts
    OUTPUT_MAX_HEIGHT = 600
    OUTPUT_MAX_WIDTH = 1600
    WEBP_QUALITY = 92

    def save(self, *args, **kwargs):

        if self.image and not self.image.name.lower().endswith(".webp"):
            self.image = self.process_image(self.image)
            
        super().save(*args, **kwargs)

    def process_image(self, image_field):
        try:
            with Image.open(image_field) as img:
                img.verify()
        except UnidentifiedImageError:
            raise ValidationError("Uploaded file is not a valid image")
            
        with Image.open(image_field) as img:
            
            if img.width > self.OUTPUT_MAX_WIDTH or img.height > self.OUTPUT_MAX_HEIGHT:
                img.thumbnail(
                    (self.OUTPUT_MAX_WIDTH, self.OUTPUT_MAX_HEIGHT),
                    Image.Resampling.LANCZOS
                )

            buffer = BytesIO()
            use_lossless = image_field.name.lower().endswith(".png")
            img.save(
                buffer,
                format="WEBP",
                quality=self.WEBP_QUALITY,
                lossless=use_lossless,
                method=6,
                optimize=True
            )

        base_name = os.path.splitext(os.path.basename(image_field.name))[0]
        new_name = f"sponsors/{base_name}-{uuid.uuid4().hex}.webp"

        return ContentFile(
            buffer.getvalue(),
            name=new_name
        )

    uploaded_at = models.DateTimeField(
        auto_now_add = True
    )
    
    class Meta:
        ordering = ["-uploaded_at"]

    def __str__(self):
        return f"{self.name} ({self.tournament.name})"