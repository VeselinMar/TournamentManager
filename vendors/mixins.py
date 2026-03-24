from django.shortcuts import get_object_or_404
from tournamentapp.models import Tournament


class TournamentFromURLMixin:
    """
    Resolves tournament from tournament_id URL kwarg.
    Raises 404 if tournament doesn't exist or doesn't belong to request.user.
    """
    def get_tournament(self):
        if not hasattr(self, '_tournament'):
            self._tournament = get_object_or_404(
                Tournament,
                pk=self.kwargs['tournament_id'],
                owner=self.request.user
            )
        return self._tournament