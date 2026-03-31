import logging
from django.urls import reverse_lazy
from django.views.generic import CreateView, UpdateView, ListView
from django.shortcuts import get_object_or_404
from django.http import JsonResponse, HttpResponseForbidden
from .models import SponsorBanner
from .forms import SponsorBannerForm
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from tournamentapp.models import Tournament


from django.urls import reverse_lazy
from django.views.generic import CreateView, UpdateView, ListView
from django.shortcuts import get_object_or_404
from django.http import JsonResponse, HttpResponseForbidden
from .models import SponsorBanner
from .forms import SponsorBannerForm
from django.views.decorators.http import require_POST, require_http_methods
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from tournamentapp.models import Tournament

logger = logging.getLogger(__name__)

class SponsorBannerCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    model = SponsorBanner
    form_class = SponsorBannerForm
    template_name = 'sponsor_form.html'

    def test_func(self):
        try:
            tournament = self.get_tournament()
            return self.request.user == tournament.owner
        except Exception as e:
            logger.exception("Error checking user permissions in test_func")
            return False

    def get_tournament(self):
        try:
            return Tournament.objects.get(pk=self.kwargs['tournament_id'])
        except Tournament.DoesNotExist:
            logger.exception(f"Tournament with id {self.kwargs.get('tournament_id')} does not exist")
            raise

    def get_initial(self):
        try:
            return {'tournament': self.get_tournament()}
        except Exception as e:
            logger.exception("Error getting initial form data")
            return {}

    def get_success_url(self):
        try:
            return reverse_lazy('sponsor-list', kwargs={'tournament_id': self.kwargs['tournament_id']})
        except Exception as e:
            logger.exception("Error determining success URL")
            return '/'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        try:
            context['tournament'] = self.get_tournament()
        except Exception as e:
            logger.exception("Error adding tournament to context")
            context['tournament'] = None
        return context

    def form_valid(self, form):
        try:
            return super().form_valid(form)
        except Exception as e:
            logger.exception("Error saving SponsorBanner form")
            return HttpResponseServerError("An unexpected error occurred. Check logs.")

class SponsorBannerListView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    model = SponsorBanner
    template_name = 'sponsor_list.html'
    context_object_name = 'banners'

    def test_func(self):
        tournament = self.get_tournament()
        return self.request.user == tournament.owner

    def get_queryset(self):
        return self.get_tournament().sponsors.all()

    def get_tournament(self):
        return Tournament.objects.get(pk=self.kwargs['tournament_id'])

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['tournament'] = self.get_tournament()
        return context

@require_http_methods(['DELETE'])
@login_required
def delete_sponsor_banner(request, tournament_id, pk):
    banner = get_object_or_404(SponsorBanner, pk=pk, tournament_id=tournament_id)

    # Restrict unauthorized access
    if banner.tournament.owner != request.user:
        return HttpResponseForbidden()

    banner.delete()
    return JsonResponse({'success': True})