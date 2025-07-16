import csv
import json
from django import forms
from django.views.decorators.http import require_POST, require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import TemplateView, DetailView, ListView
from django.views.generic.edit import CreateView, UpdateView
from django.http import JsonResponse
from django.contrib import messages
from django.shortcuts import redirect, get_object_or_404
from .models import Match, Team, GoalEvent, Player, MatchEvent, Field
from .forms import TeamCreateForm, MatchCreateForm, MatchEditForm, MatchEventForm, FieldCreateForm
from django.urls import reverse_lazy
from django.db.models import Q, Count
from collections import defaultdict
from django.utils.timezone import localtime


class HomePageView(TemplateView):
    template_name = 'home.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        matches = Match.objects.select_related('field', 'home_team', 'away_team').order_by('start_time')

        # Get all field names and unique times
        all_field_names = sorted({match.field.name for match in matches})
        matches_by_time = defaultdict(dict)

        for match in matches:
            time_key = localtime(match.start_time).strftime("%H:%M")
            matches_by_time[time_key][match.field.name] = match

        timeline = []
        for time, field_dict in sorted(matches_by_time.items()):
            row = {
                'time': time,
                'matches': [field_dict.get(fname) for fname in all_field_names]
            }
            timeline.append(row)

        context.update({
            'timeline': timeline,
            'field_names': all_field_names,
        })

        return context

class TeamListView(ListView):
    model = Team
    template_name = 'teams/team_list.html'
    context_object_name = 'teams'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['teams'] = Team.objects.all().order_by('name')
        return context

class TeamDetailView(DetailView):
    model = Team
    template_name = 'teams/team_detail.html'
    context_object_name = 'team'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        team = self.object

        # Get matches for the team
        all_matches = Match.objects.filter(
            Q(home_team=team) | Q(away_team=team)
        ).order_by('start_time')

        # Determine finished match results
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
    form_class = TeamCreateForm
    template_name = 'teams/team_form.html'
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
    form_class = MatchCreateForm
    template_name = 'matches/match_create.html'
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

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        team = self.object.home_team if request.POST['team'] == 'home' else self.object.away_team
        player_name = request.POST['player_name'].strip()
        minute = request.POST['minute'].strip()

        player, _ = Player.objects.get_or_create(name=player_name, team=team)
        MatchEvent.objects.create(
            match=self.object,
            event_type=request.POST['event_type'],
            minute=minute,
            team=team,
            player=player
        )
        return redirect('match-detail', pk=self.object.pk)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        match = self.object
        context['match_events'] = match.events.all()
        return context

class LeaderboardView(TemplateView):
    template_name = 'matches/leaderboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Top scorers
        players = Player.objects.filter(goals__gt=0).order_by('-goals')[:10]
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

class FieldAddView(CreateView):
    model = Field
    form_class = FieldCreateForm
    template_name = 'fields/field_create.html'
    success_url = reverse_lazy('field-create')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['fields'] = Field.objects.all()
        return context
        

@require_POST
def create_match_event(request, match_id):
    event_type = request.POST.get('event_type')
    team_side = request.POST.get('team')
    player_id = request.POST.get('player_id')
    minute = request.POST.get('minute', '0')

    match = get_object_or_404(Match, id=match_id)
    team = match.home_team if team_side == 'home' else match.away_team
    player = get_object_or_404(Player, id=player_id, team=team)

    event = MatchEvent.objects.create(
        match=match,
        team=team,
        player=player,
        event_type=event_type,
        minute=minute,
    )

    # Recalculate score without finalizing the match
    home_score = match.events.filter(event_type='goal', team=match.home_team).count()
    home_score += match.events.filter(event_type='own_goal', team=match.away_team).count()

    away_score = match.events.filter(event_type='goal', team=match.away_team).count()
    away_score += match.events.filter(event_type='own_goal', team=match.home_team).count()

    return JsonResponse({
        'success': True,
        'player_name': player.name,
        'event_type': event_type,
        'home_score': home_score,
        'away_score': away_score,
        'event': {
            'id': event.id,
            'player_name': player.name,
            'event_type': event_type,
            'timestamp': f"{minute}'"
        }
    })

@csrf_exempt
def add_player(request, team_id):
    if request.method == 'POST':
        player_name = request.POST.get('player')
        if not player_name:
            return JsonResponse({'success': False, 'error': 'Player name is required.'}, status=400)

        try:
            team = get_object_or_404(Team, id=team_id)
        except Team.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Team not found.'}, status=404)

        player, created = Player.objects.get_or_create(name=player_name.strip(), team=team)

        return JsonResponse({
            'success': True,
            'player': {
                'id': player.id,
                'name': player.name,
                'team': team.name
            }
        })
    return JsonResponse({'success': False, 'error': 'Invalid request method'}, status=405)

@require_POST
def finish_match(request, match_id):
    match = get_object_or_404(Match, id=match_id)

    if not match.is_finished:
        match.apply_result()

    return redirect('match-detail', pk=match_id)

@require_http_methods(['DELETE'])
def remove_match_event(request, event_id):
    event = get_object_or_404(MatchEvent, id=event_id)
    match = event.match

    # Delete the event
    event.delete()

    # Recalculate score after deletion
    home_score = match.events.filter(event_type='goal', team=match.home_team).count()
    home_score += match.events.filter(event_type='own_goal', team=match.away_team).count()

    away_score = match.events.filter(event_type='goal', team=match.away_team).count()
    away_score += match.events.filter(event_type='own_goal', team=match.home_team).count()

    return JsonResponse({
        'success': True,
        'home_score': home_score,
        'away_score': away_score,
    })

@require_POST
def field_edit(request, pk):
    field = get_object_or_404(Field, pk=pk)

    try:
        data = json.loads(request.body)
        new_name = data.get('name', '').strip()
    except (json.JSONDecodeError, AttributeError):
        return JsonResponse({'success': False, 'error': 'Invalid JSON'})

    if not new_name:
        return JsonResponse({'success': False, 'error': 'Field name cannot be empty.'})

    field.name = new_name
    field.save()
    return JsonResponse({'success': True, 'name': field.name})


@require_POST
def field_delete(request, pk):
    field = get_object_or_404(Field, pk=pk)

    if field.match_set.exists():
        return JsonResponse({'success': False, 'error': 'Cannot delete field with assigned matches.'})

    field.delete()
    return JsonResponse({'success': True})