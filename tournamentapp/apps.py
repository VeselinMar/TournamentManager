from django.apps import AppConfig
from django.db import OperationalError, ProgrammingError


class TournamentappConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'tournamentapp'
    verbose_name = "Tournament Manager"
    
    def ready(self):
        # Import signals to ensure they are registered
        import tournamentapp.signals
        from tournamentapp.models import Field 
        try:
            if not Field.objects.filter(name='Main Field').exists():
                Field.objects.create(name='Main Field')
        except (OperationalError, ProgrammingError) as e:
            pass