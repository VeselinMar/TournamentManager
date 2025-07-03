from django.views.generic import TemplateView, DetailView, ListView
from django.views.generic.edit import CreateView, UpdateView
from .models import Match, Team, GoalEvent, Player
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
            'matches': Match.objects.all().order_by('start_time'),
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

        home_goals = GoalEvent.objects.filter(match=match, team=match.home_team).count()
        away_goals = GoalEvent.objects.filter(match=match, team=match.away_team).count()
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

class TeamLeaderboardView(ListView):
    model = Team
    template_name = 'matches/team_leaderboard.html'
    context_object_name = 'teams'

    def get_queryset(self):
        teams = list(Team.objects.all())

        # Step 1: Group teams by tournament points
        points_groups = {}
        for team in teams:
            points_groups.setdefault(team.tournament_points, []).append(team)

        sorted_teams = []

        # Step 2: Sort each group
        for points in sorted(points_groups.keys(), reverse=True):
            group = points_groups[points]

            if len(group) == 1:
                sorted_teams.extend(group)
                continue

            # Step 3: For tied teams, compute goal difference in their mutual matches
            for team in group:
                opponents = [t for t in group if t != team]
                mutual_matches = Match.objects.filter(
                    is_finished=True &
                    (
                        Q(home_team=team, away_team__in=opponents) |
                        Q(away_team=team, home_team__in=opponents)
                    )
                )

                goals_for = MatchEvent.objects.filter(
                    match__in=mutual_matches,
                    team=team,
                    event_type='goal'
                ).count()

                goals_against = MatchEvent.objects.filter(
                    match__in=mutual_matches,
                    match__home_team=team
                ).exclude(team=team).filter(event_type='goal').count() + \
                MatchEvent.objects.filter(
                    match__in=mutual_matches,
                    match__away_team=team
                ).exclude(team=team).filter(event_type='goal').count()

                team.goal_difference_vs_tied = goals_for - goals_against

            # Sort tied teams by head-to-head goal difference and name
            group.sort(key=lambda t: (-t.goal_difference_vs_tied, t.name))
            sorted_teams.extend(group)

        return sorted_teams
