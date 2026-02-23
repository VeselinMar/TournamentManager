from django.apps import AppConfig
from django.db.models.signals import post_migrate

class TournamentappConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'tournamentapp'
    verbose_name = "Tournament Manager"

    def ready(self):
        from . import signals  # import signals normally
        from .models import Field, Tournament
        from django.db import OperationalError, ProgrammingError

        def create_default_field(sender, **kwargs):
            try:
                if not Field.objects.filter(name="Main Field").exists():
                    tournament = Tournament.objects.first()
                    if tournament:
                        Field.objects.create(
                            name="Main Field",
                            tournament=tournament,
                            owner=tournament.owner
                        )
            except (OperationalError, ProgrammingError):
                pass

        post_migrate.connect(create_default_field, sender=self)