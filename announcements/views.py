from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.urls import reverse

from vendors.mixins import TournamentFromURLMixin
from .models import Announcement
from .forms import AnnouncementForm


class AnnouncementListView(LoginRequiredMixin, TournamentFromURLMixin, ListView):
    model = Announcement
    template_name = 'announcements/announcement_list.html'
    context_object_name = 'announcements'

    def get_queryset(self):
        return Announcement.objects.filter(tournament=self.get_tournament())

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['tournament'] = self.get_tournament()
        return context


class AnnouncementCreateView(LoginRequiredMixin, TournamentFromURLMixin, CreateView):
    model = Announcement
    form_class = AnnouncementForm
    template_name = 'announcements/announcement_form.html'

    def form_valid(self, form):
        form.instance.tournament = self.get_tournament()
        return super().form_valid(form)

    def get_success_url(self):
        return reverse('announcement-list', kwargs={'tournament_id': self.get_tournament().pk})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['tournament'] = self.get_tournament()
        return context


class AnnouncementUpdateView(LoginRequiredMixin, TournamentFromURLMixin, UpdateView):
    model = Announcement
    form_class = AnnouncementForm
    template_name = 'announcements/announcement_form.html'

    def get_object(self, queryset=None):
        return get_object_or_404(
            Announcement,
            pk=self.kwargs['pk'],
            tournament=self.get_tournament()
        )

    def get_success_url(self):
        return reverse('announcement-list', kwargs={'tournament_id': self.get_tournament().pk})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['tournament'] = self.get_tournament()
        return context


class AnnouncementDeleteView(LoginRequiredMixin, TournamentFromURLMixin, DeleteView):
    model = Announcement
    template_name = 'announcements/announcement_confirm_delete.html'

    def get_object(self, queryset=None):
        return get_object_or_404(
            Announcement,
            pk=self.kwargs['pk'],
            tournament=self.get_tournament()
        )

    def get_success_url(self):
        return reverse('announcement-list', kwargs={'tournament_id': self.get_tournament().pk})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['tournament'] = self.get_tournament()
        return context