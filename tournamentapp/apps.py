from django.apps import AppConfig
from django.db import OperationalError, ProgrammingError


class TournamentappConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'tournamentapp'
    verbose_name = "Tournament Manager"
    
    def ready(self):
        import tournamentapp.signals
        from tournamentapp.models import Field, Tournament
        
        try:
            if not Field.objects.filter(name='Main Field').exists():
                tournament = Tournament.objects.first()
                if tournament:
                    Field.objects.create(
                        name='Main Field',
                        tournament=tournament,
                        owner=tournament.owner)
        except (OperationalError, ProgrammingError):
            pass