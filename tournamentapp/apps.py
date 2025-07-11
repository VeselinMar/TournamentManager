from django.apps import AppConfig


class TournamentappConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'tournamentapp'
    verbose_name = "Tournament Manager"
    
    def ready(self):
        # Import signals to ensure they are registered
        import tournamentapp.signals