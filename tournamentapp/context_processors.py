from .models import Tournament

def current_tournament(request):
    if request.user.is_authenticated:
        return {
            'user_tournament': Tournament.objects.filter(owner=request.user).first()
        }
    return {}