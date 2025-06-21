from django.views.generic import TemplateView, DetailView, ListView
from django.views.generic.edit import CreateView, UpdateView
from .models import Match, Team, Goal, Player
from .forms import TeamForm, MatchForm, MatchEditForm
from django.urls import reverse_lazy


class HomePageView(TemplateView):
    template_name = 'matches/home.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        teams = Team.objects.all()
        matches_exist = Match.objects.exists()

        context.update({
            'teams': teams,
            'field_a_matches': Match.objects.filter(field='A').order_by('start_time'),
            'field_b_matches': Match.objects.filter(field='B').order_by('start_time'),
            'no_teams': not teams.exists(),
            'no_matches': not matches_exist,
        })

        return context

class TeamCreateView(CreateView):
    model = Team
    form_class = TeamForm
    template_name = 'matches/team_form.html'
    success_url = reverse_lazy('home')

class MatchCreateView(CreateView):
    model = Match
    form_class = MatchForm
    template_name = 'matches/match_form.html'
    success_url = reverse_lazy('home')

class MatchDetailView(DetailView):
    model = Match
    template_name = 'matches/match_detail.html'
    context_object_name = 'match'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        match = self.object

        context['goals'] = Goal.objects.filter(match=match)
        return context

class MatchEditView(UpdateView):
    model = Match
    form_class = MatchEditForm
    template_name = 'matches/match_edit.html'
    success_url = reverse_lazy('home')

class TopScorersView(ListView):
    model = Player
    template_name = 'matches/top_scorers.html'
    context_object_name = 'players'
    queryset = Player.objects.all().order_by('-goals')