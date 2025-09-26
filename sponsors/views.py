from django.urls import reverse_lazy
from django.views.generic import CreateView, UpdateView, ListView
from .models import SponsorBanner
from .forms import SponsorBannerForm
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from tournamentapp.models import Tournament


class SponsorBannerCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    model = SponsorBanner
    form_class = SponsorBannerForm
    template_name = 'sponsor_form.html'

    def test_func(self):
        tournament = self.get_tournament()
        return self.request.user == tournament.owner

    def get_tournament(self):
        return Tournament.objects.get(pk=self.kwargs['tournament_id'])

    def get_initial(self):
        return {'tournament': self.get_tournament()}

    def get_success_url(self):
        return reverse_lazy('sponsor-list', kwargs={'tournament_id': self.kwargs['tournament_id']})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['tournament'] = self.get_tournament()
        return context

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