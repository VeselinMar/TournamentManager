from django.apps import AppConfig

class TournamentappConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'tournamentapp'
    verbose_name = "Tournament Manager"

    def ready(self):
        from . import signals  # noqa: F401  (connects cache invalidation)
