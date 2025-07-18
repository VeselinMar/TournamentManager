from .models import Tournament

def current_tournament(request):
    tournament = Tournament.objects.first()
    return {'tournament': tournament}