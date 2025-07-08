import csv
from django import forms
from django.views.generic import TemplateView, DetailView, ListView
from django.views.generic.edit import CreateView, UpdateView
from django.contrib import messages
from django.shortcuts import redirect
from .models import Match, Team, GoalEvent, Player, MatchEvent, Field
from .forms import TeamForm, MatchForm, MatchEditForm
from django.urls import reverse_lazy
from django.db.models import Q


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

class TeamListView(ListView):
    model = Team
    template_name = 'matches/team_list.html'
    context_object_name = 'teams'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['teams'] = Team.objects.all().order_by('name')
        return context

class TeamDetailView(DetailView):
    model = Team
    template_name = 'matches/team_detail.html'
    context_object_name = 'team'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        team = self.object

        # Get matches for the team
        all_matches = Match.objects.filter(
            Q(home_team=team) | Q(away_team=team)
        ).order_by('start_time')

        # Determine fini match results
        finished_matches = []
        for match in all_matches.filter(is_finished=True):
            is_home = match.home_team == team
            team_score = match.home_score if is_home else match.away_score
            opponent_score = match.away_score if is_home else match.home_score
            if team_score > opponent_score:
                match.result = 'win'
            elif team_score < opponent_score:
                match.result = 'loss'
            else:
                match.result = 'draw'
            match.goal_difference = abs(team_score - opponent_score)
            finished_matches.append(match)

        # Split matches into finished and upcoming
        context['finished_matches'] = finished_matches
        context['upcoming_matches'] = all_matches.filter(is_finished=False)

        # Get players in the team
        context['players'] = team.players.all()

        return context

class TeamCreateView(CreateView):
    model = Team
    form_class = TeamForm
    template_name = 'matches/team_form.html'
    success_url = reverse_lazy('home')

    def post(self, request, *args, **kwargs):
        if request.POST.get('submit_type') == 'batch':
            csv_file = request.FILES.get('csv_file')
            if not csv_file or not csv_file.name.lower().endswith('.csv'):
                messages.error(request, 'Please upload a valid CSV file.')
                return redirect('team-create')

            try:
                decoded_file = csv_file.read().decode('utf-8').splitlines()
                reader = csv.reader(decoded_file)
                created = 0
                for row in reader:
                    if row:
                        name = row[0].strip()
                        form = TeamForm(data={'name': name})
                        if form.is_valid():
                            form.save()
                            created += 1
                        else:
                            # Optionally collect and show form errors
                            messages.warning(request, f"Skipped invalid entry '{name}': {form.errors['name'][0]}")
                messages.success(request, f'{created} team(s) successfully created.')
            except Exception as e:
                messages.error(request, f'Error processing CSV file: {str(e)}')

            return redirect('team-create')

        return super().post(request, *args, **kwargs)

class MatchCreateView(CreateView):
    model = Match
    form_class = MatchForm
    template_name = 'matches/match_form.html'
    success_url = reverse_lazy('home')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['fields'] = Field.objects.all()
        return context

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

class LeaderboardView(TemplateView):
    template_name = 'matches/leaderboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Top scorers
        players = Player.objects.all().order_by('-goals')
        context['players'] = players

        # Team leaderboard (same logic from TeamLeaderboardView)
        teams = list(Team.objects.all())
        points_groups = {}
        for team in teams:
            points_groups.setdefault(team.tournament_points, []).append(team)

        sorted_teams = []

        for points in sorted(points_groups.keys(), reverse=True):
            group = points_groups[points]

            if len(group) == 1:
                sorted_teams.extend(group)
                continue

            for team in group:
                opponents = [t for t in group if t != team]
                mutual_matches = Match.objects.filter(
                    is_finished=True
                ).filter(
                    Q(home_team=team, away_team__in=opponents) |
                    Q(away_team=team, home_team__in=opponents)
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

            group.sort(key=lambda t: (-t.goal_difference_vs_tied, t.name))
            sorted_teams.extend(group)

        context['teams'] = sorted_teams
        return context