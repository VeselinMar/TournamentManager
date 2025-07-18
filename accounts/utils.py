from django.urls import reverse
from tournamentapp.models import Tournament

def get_post_login_redirect(user):
    tournament = (
        Tournament.objects
        .filter(owner=user, is_finished=False)
        .first()
    )
    if tournament:
        return reverse('tournament-detail', kwargs={'pk': tournament.pk})
    
    return reverse('tournament-create')