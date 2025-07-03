from django.db.models.signals import pre_save
from django.dispatch import receiver
from .models import Player

@receiver(pre_save, sender=Player)
def apply_card_rules(sender, instance, **kwargs):
    # Assign a red card if 2 yellow cards and no red card
    if instance.yellow_cards >= 2 and instance.red_cards == 0:
        instance.red_cards = 1

    # Update eligibility based on final card values
    instance.update_eligibility()