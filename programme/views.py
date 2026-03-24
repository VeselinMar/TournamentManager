from django.shortcuts import render

from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.urls import reverse

from vendors.mixins import TournamentFromURLMixin
from .models import SideEvent
from .forms import SideEventForm


class SideEventListView(LoginRequiredMixin, TournamentFromURLMixin, ListView):
    model = SideEvent
    template_name = 'programme/sideevent_list.html'
    context_object_name = 'side_events'

    def get_queryset(self):
        return SideEvent.objects.filter(tournament=self.get_tournament())

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['tournament'] = self.get_tournament()
        return context


class SideEventCreateView(LoginRequiredMixin, TournamentFromURLMixin, CreateView):
    model = SideEvent
    form_class = SideEventForm
    template_name = 'programme/sideevent_form.html'

    def form_valid(self, form):
        form.instance.tournament = self.get_tournament()
        return super().form_valid(form)

    def get_success_url(self):
        return reverse('sideevent-list', kwargs={'tournament_id': self.get_tournament().pk})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['tournament'] = self.get_tournament()
        return context


class SideEventUpdateView(LoginRequiredMixin, TournamentFromURLMixin, UpdateView):
    model = SideEvent
    form_class = SideEventForm
    template_name = 'programme/sideevent_form.html'

    def get_object(self, queryset=None):
        return get_object_or_404(
            SideEvent,
            pk=self.kwargs['pk'],
            tournament=self.get_tournament()
        )

    def get_success_url(self):
        return reverse('sideevent-list', kwargs={'tournament_id': self.get_tournament().pk})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['tournament'] = self.get_tournament()
        return context


class SideEventDeleteView(LoginRequiredMixin, TournamentFromURLMixin, DeleteView):
    model = SideEvent
    template_name = 'programme/sideevent_confirm_delete.html'

    def get_object(self, queryset=None):
        return get_object_or_404(
            SideEvent,
            pk=self.kwargs['pk'],
            tournament=self.get_tournament()
        )

    def get_success_url(self):
        return reverse('sideevent-list', kwargs={'tournament_id': self.get_tournament().pk})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['tournament'] = self.get_tournament()
        return context