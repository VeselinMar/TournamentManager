from django.shortcuts import get_object_or_404

from .models import Tournament

class TournamentOwnerMixin:
    def get_queryset(self):
        return Tournament.objects.filter(owner=self.request.user)

class TournamentAccessMixin:
    def get_tournament(self):
        if not hasattr(self, "_tournament"):
            self._tournament = get_object_or_404(
                Tournament,
                pk=self.kwargs.get("tournament_id"),
                owner=self.request.user
            )
        return self._tournament