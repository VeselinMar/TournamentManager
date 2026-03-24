from django.shortcuts import render

from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.urls import reverse

from tournamentapp.models import Tournament
from vendors.mixins import TournamentFromURLMixin
from .models import Vendor
from .forms import VendorForm


class VendorListView(LoginRequiredMixin, TournamentFromURLMixin, ListView):
    model = Vendor
    template_name = 'vendor_list.html'
    context_object_name = 'vendors'

    def get_queryset(self):
        return Vendor.objects.filter(tournament=self.get_tournament())

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['tournament'] = self.get_tournament()
        return context


class VendorCreateView(LoginRequiredMixin, TournamentFromURLMixin, CreateView):
    model = Vendor
    form_class = VendorForm
    template_name = 'vendor_form.html'

    def form_valid(self, form):
        form.instance.tournament = self.get_tournament()
        return super().form_valid(form)

    def get_success_url(self):
        return reverse('vendor-list', kwargs={'tournament_id': self.get_tournament().pk})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['tournament'] = self.get_tournament()
        return context


class VendorUpdateView(LoginRequiredMixin, TournamentFromURLMixin, UpdateView):
    model = Vendor
    form_class = VendorForm
    template_name = 'vendor_form.html'

    def get_object(self, queryset=None):
        return get_object_or_404(
            Vendor,
            pk=self.kwargs['pk'],
            tournament=self.get_tournament()
        )

    def get_success_url(self):
        return reverse('vendor-list', kwargs={'tournament_id': self.get_tournament().pk})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['tournament'] = self.get_tournament()
        return context


class VendorDeleteView(LoginRequiredMixin, TournamentFromURLMixin, DeleteView):
    model = Vendor
    template_name = 'vendor_confirm_delete.html'

    def get_object(self, queryset=None):
        return get_object_or_404(
            Vendor,
            pk=self.kwargs['pk'],
            tournament=self.get_tournament()
        )

    def get_success_url(self):
        return reverse('vendor-list', kwargs={'tournament_id': self.get_tournament().pk})