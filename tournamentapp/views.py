import csv
import json
from django import forms
from django.views.decorators.http import require_POST, require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import TemplateView, DetailView, ListView
from django.views.generic.edit import CreateView, UpdateView
from django.http import JsonResponse, HttpResponseForbidden, Http404
from django.utils.timezone import localtime
from django.utils import timezone
from datetime import timedelta
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, get_object_or_404, render
from .models import Match, Team, GoalEvent, Player, MatchEvent, Field, Tournament
from .forms import TeamCreateForm, MatchCreateForm, MatchEditForm, MatchEventForm, FieldCreateForm, TournamentCreateForm,TournamentScheduleForm
from django.urls import reverse_lazy, reverse
from django.db.models import Q, Count
from collections import defaultdict
from django.utils.timezone import localtime, datetime
from formtools.wizard.views import SessionWizardView
from .utils import handle_batch_lines, create_round_robin_matches


class TournamentCreateView(CreateView, LoginRequiredMixin):
    model = Tournament
    form_class = TournamentCreateForm
    template_name = 'tournament/tournament_form.html'

    def dispatch(self, request, *args, **kwargs):
        if Tournament.objects.filter(owner=self.request.user).exists():
            tournament = Tournament.objects.get(owner=self.request.user)
            return redirect('tournament-detail', pk=tournament.pk)
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        form.instance.owner = self.request.user
        return super().form_valid(form)

    def get_success_url(self):
        return reverse('team-create', kwargs={'tournament_id': self.object.pk})

class TournamentPublicView(DetailView):
    model = Tournament
    template_name = 'tournament/public_home.html'
    slug_field = 'slug'
    slug_url_kwarg = 'slug'

    def get_object(self, queryset=None):
        slug = self.kwargs.get(self.slug_url_kwarg)
        return get_object_or_404(Tournament, slug=slug)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        tournament = self.object

        today = datetime.today().date()
        matches_today = (
            tournament.matches
            .select_related('field', 'home_team', 'away_team')
            .filter(start_time__date=today)
            .order_by('start_time')
        )

        field_names = list(
            tournament.fields.order_by('name').values_list('name', flat=True)
        )

        timeline_dict = defaultdict(lambda: {field: None for field in field_names})

        for match in matches_today:
            time_str = match.start_time.strftime('%H:%M')
            timeline_dict[time_str][match.field.name] = match

        timeline = [
            {
                'time': time_str,
                'matches': [timeline_dict[time_str][field] for field in field_names],
            }
            for time_str in sorted(timeline_dict.keys())
        ]

        context.update({
            'timeline': timeline,
            'field_names': field_names,
        })

        return context

class TournamentDetailView(LoginRequiredMixin, TemplateView):
    template_name = 'tournament/tournament_detail.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        tournament_id = self.kwargs.get('pk')
        tournament = get_object_or_404(Tournament, pk=tournament_id, owner=self.request.user)

        matches = Match.objects.filter(tournament=tournament).select_related('field', 'home_team', 'away_team').order_by('start_time')
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
            'tournament': tournament,
        })
        return context

class LandingPageView(TemplateView):
    template_name = 'tournament/landing_page.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['tournaments'] = Tournament.objects.filter(is_finished=False)
        return context

class TeamListView(LoginRequiredMixin, ListView):
    model = Team
    template_name = 'teams/team_list.html'
    context_object_name = 'teams'

    def get_queryset(self):
        tournament_id = self.kwargs.get('tournament_id')
        tournament = get_object_or_404(Tournament, pk=tournament_id, owner=self.request.user)
        return Team.objects.filter(tournament=tournament).order_by('name')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        tournament_id = self.kwargs.get('tournament_id')
        tournament = get_object_or_404(Tournament, pk=tournament_id, owner=self.request.user)
        context['tournament'] = tournament
        return context

class TeamDetailView(DetailView):
    model = Team
    template_name = 'teams/team_detail.html'
    context_object_name = 'team'

    def get_object(self, queryset=None):
        tournament_id = self.kwargs.get('tournament_id')
        team_pk = self.kwargs.get('pk')

        tournament = get_object_or_404(Tournament, pk=tournament_id)

        # Get the team belonging to that tournament
        team = get_object_or_404(Team, pk=team_pk, tournament=tournament)

        return team

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

        # Also add tournament for context usage
        context['tournament'] = team.tournament

        return context

class TeamCreateView(LoginRequiredMixin, CreateView):
    model = Team
    form_class = TeamCreateForm
    template_name = 'teams/team_form.html'

    def dispatch(self, request, *args, **kwargs):
        # Get tournament and check ownership
        self.tournament_id = kwargs.get('tournament_id')
        self.tournament = get_object_or_404(Tournament, pk=self.tournament_id, owner=request.user)
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Pass all teams for this tournament to the template
        context['tournament'] = self.tournament
        context['teams'] = self.tournament.teams.all().prefetch_related('player_set')
        return context

    def get_success_url(self):
        return reverse('team-list', kwargs={'tournament_id': self.tournament.pk})

    def post(self, request, *args, **kwargs):
        submit_type = request.POST.get('submit_type')

        # ===========================
        # CSV batch upload
        # ===========================
        if submit_type == 'batch' and request.FILES.get('csv_file'):
            csv_file = request.FILES['csv_file']
            if not csv_file.name.lower().endswith('.csv'):
                messages.error(request, 'Please upload a valid CSV file.')
                return redirect('team-create', tournament_id=self.tournament.pk)

            try:
                decoded_lines = csv_file.read().decode('utf-8').splitlines()
                created_teams, created_players = handle_batch_lines(request, self.tournament, decoded_lines)
                messages.success(request, f'{created_teams} team(s) and {created_players} player(s) successfully created.')
            except Exception as e:
                messages.error(request, f'Error processing CSV file: {str(e)}')

            return redirect('team-create', tournament_id=self.tournament.pk)

        # ===========================
        # Multi-line textarea input
        # ===========================
        elif submit_type != 'batch':
            multiline_input = request.POST.get('name', '').splitlines()
            if not multiline_input:
                messages.error(request, 'Please enter at least one team.')
                return redirect('team-create', tournament_id=self.tournament.pk)

            created_teams, created_players = handle_batch_lines(request, self.tournament, multiline_input)
            messages.success(request, f'{created_teams} team(s) and {created_players} player(s) successfully created.')
            return redirect('team-create', tournament_id=self.tournament.pk)

        # ===========================
        # Fallback: default CreateView behavior
        # ===========================
        return super().post(request, *args, **kwargs)

class MatchCreateView(LoginRequiredMixin, CreateView):
    model = Match
    form_class = MatchCreateForm
    template_name = 'matches/match_create.html'

    def dispatch(self, request, *args, **kwargs):
        self.tournament_id = kwargs.get('tournament_id')
        self.tournament = get_object_or_404(Tournament, pk=self.tournament_id, owner=request.user)
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['fields'] = Field.objects.filter(tournament=self.tournament)
        context['tournament'] = self.tournament
        return context
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['tournament'] = self.tournament
        return kwargs

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        form.instance.tournament = self.tournament
        return form
    

    def get_success_url(self):
        return reverse('tournament-detail', kwargs={'pk': self.tournament.pk})

class MatchDetailView(LoginRequiredMixin, DetailView):
    model = Match
    template_name = 'matches/match_detail.html'
    context_object_name = 'match'

    def dispatch(self, request, *args, **kwargs):
        self.tournament_id = kwargs.get('tournament_id')
        self.tournament = get_object_or_404(Tournament, pk=self.tournament_id, owner=request.user)
        return super().dispatch(request, *args, **kwargs)

    def get_object(self, queryset=None):
        match = super().get_object(queryset)
        if match.tournament_id != self.tournament.pk:
            raise Http404("Match does not belong to this tournament.")
        return match

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        match = self.object

        home_goals = GoalEvent.objects.filter(match=match, team=match.home_team).count()
        away_goals = GoalEvent.objects.filter(match=match, team=match.away_team).count()

        context.update({
            'home_goals': home_goals,
            'away_goals': away_goals,
            'tournament': self.tournament,
        })
        return context

class MatchEditView(LoginRequiredMixin, UpdateView):
    model = Match
    form_class = MatchEditForm
    template_name = 'matches/match_edit.html'

    def dispatch(self, request, *args, **kwargs):
        self.tournament_id = kwargs.get('tournament_id')
        self.tournament = get_object_or_404(Tournament, pk=self.tournament_id, owner=request.user)
        match = self.get_object()
        if match.tournament_id != self.tournament.pk:
            return HttpResponseForbidden()
        return super().dispatch(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        team = self.object.home_team if request.POST.get('team') == 'home' else self.object.away_team
        player_name = request.POST.get('player_name', '').strip()
        minute = request.POST.get('minute', '').strip()

        # Handled in match_edit.js
        # if player_name:
        #     player, _ = Player.objects.get_or_create(name=player_name, team=team)
        #     MatchEvent.objects.create(
        #         match=self.object,
        #         event_type=request.POST.get('event_type'),
        #         minute=minute,
        #         team=team,
        #         player=player
        #     )
        # return redirect('public/<slug:slug>/', tournament_id=self.tournament.pk, pk=self.object.pk)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        match = self.object
        context['match_events'] = match.events.all()
        context['tournament'] = self.tournament
        return context

class LeaderboardView(TemplateView):
    template_name = 'matches/leaderboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        tournament_id = self.kwargs.get('tournament_id')
        tournament = get_object_or_404(Tournament, id=tournament_id)

        # Top scorers from this tournament only
        players = Player.objects.filter(
            team__tournament=tournament,
            goals__gt=0
        ).order_by('-goals')[:10]
        context['players'] = players

        # Get teams from this tournament
        teams = list(Team.objects.filter(tournament=tournament))
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
                    is_finished=True,
                    tournament=tournament
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
                    event_type='goal'
                ).exclude(team=team).count()

                team.goal_difference_vs_tied = goals_for - goals_against

            group.sort(key=lambda t: (-t.goal_difference_vs_tied, t.name))
            sorted_teams.extend(group)

        context['teams'] = sorted_teams
        context['tournament'] = tournament
        return context

class FieldAddView(LoginRequiredMixin, CreateView):
    model = Field
    form_class = FieldCreateForm
    template_name = 'fields/field_create.html'

    def dispatch(self, request, *args, **kwargs):
        self.tournament = get_object_or_404(Tournament, id=self.kwargs['tournament_id'])

        if self.tournament.owner != request.user:
            return HttpResponseForbidden()

        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        form.instance.tournament = self.tournament
        form.instance.owner = self.request.user
        return super().form_valid(form)

    def get_success_url(self):
        # Redirect back to the same add-field page with the tournament context
        return reverse_lazy('field-create', kwargs={'tournament_id': self.tournament.id})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['fields'] = Field.objects.filter(tournament=self.tournament)
        context['tournament'] = self.tournament
        return context

@require_POST
@login_required
def create_match_event(request, tournament_id, match_id):
    tournament = get_object_or_404(Tournament, id=tournament_id)

    if tournament.owner != request.user:
        return JsonResponse({'success': False, 'error': 'Forbidden'}, status=403)

    match = get_object_or_404(Match, id=match_id, tournament=tournament)

    event_type = request.POST.get('event_type')
    team_side = request.POST.get('team')
    player_id = request.POST.get('player_id')
    team_id = request.POST.get('team_id')
    minute = request.POST.get('minute', '0')

    if not player_id or not team_id:
        return JsonResponse({'success': False, 'error': 'Missing player_id or team_id'}, status=400)

    try:
        team_id = int(team_id)
    except ValueError:
        return JsonResponse({'success': False, 'error': 'Invalid team_id'}, status=400)

    # Decide if home or away team was referenced
    team = match.home_team if team_side == 'home' else match.away_team
    player = get_object_or_404(Player, id=player_id)

    if player.team.id != team_id:
        return JsonResponse({'success': False, 'error': 'Player does not belong to this team'}, status=400)

    # Create the event
    event = MatchEvent.objects.create(
        match=match,
        team=team,
        player=player,
        event_type=event_type,
        minute=minute,
    )
    
    event.apply_event_effects()

    # Recalculate scores
    home_score = (
        match.events.filter(event_type='goal', team=match.home_team).count() +
        match.events.filter(event_type='own_goal', team=match.away_team).count()
    )
    away_score = (
        match.events.filter(event_type='goal', team=match.away_team).count() +
        match.events.filter(event_type='own_goal', team=match.home_team).count()
    )

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

@login_required
def add_player(request, tournament_id, team_id):
    tournament = get_object_or_404(Tournament, id=tournament_id)
    if tournament.owner != request.user:
        return JsonResponse({'success': False, 'error': 'Forbidden'}, status=403)

    team = get_object_or_404(Team, id=team_id, tournament=tournament)

    if request.method == 'POST':
        player_name = request.POST.get('player')
        if not player_name:
            return JsonResponse({'success': False, 'error': 'Player name is required.'}, status=400)

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
@login_required
def finish_match(request, tournament_id, match_id):
    tournament = get_object_or_404(Tournament, id=tournament_id)
    if tournament.owner != request.user:
        return JsonResponse({'success': False, 'error': 'Forbidden'}, status=403)

    match = get_object_or_404(Match, id=match_id, tournament=tournament)

    if not match.is_finished:
        match.apply_result()

    return redirect('match-detail', tournament_id=tournament_id, pk=match_id)

@require_http_methods(['DELETE'])
@login_required
def remove_match_event(request, tournament_id, event_id):
    event = get_object_or_404(MatchEvent, id=event_id)
    match = event.match

    # Verify tournament ownership
    if match.tournament.owner != request.user or match.tournament.id != tournament_id:
        return JsonResponse({'success': False, 'error': 'Forbidden'}, status=403)

    player = event.player
    team = event.team
    event_type = event.event_type

    # Reverse consequences
    if player:
        if event_type == 'goal':
            player.goals = max(0, player.goals - 1)
            player.save()
        elif event_type == 'own_goal':
            player.own_goals = max(0, player.own_goals - 1)
            player.save()
        elif event_type == 'yellow_card':
            player.yellow_cards = max(0, player.yellow_cards - 1)
            player.save()
        elif event_type == 'red_card':
            player.red_cards = max(0, player.red_cards - 1)
            player.save()

    # Delete the event
    event.delete()

    # Reset match to unfinished state
    match.is_finished = False
    match.home_score = 0
    match.away_score = 0
    match.save()

    # Recalculate match results based on remaining events
    match.apply_result()  # your existing method to recompute scores

    return JsonResponse({
        'success': True,
        'home_score': match.home_score,
        'away_score': match.away_score,
    })

@require_POST
@login_required
def field_edit(request, tournament_id, pk):
    field = get_object_or_404(Field, pk=pk, tournament_id=tournament_id)

    # Restrict unauthorized access
    if field.tournament.owner != request.user:
        return HttpResponseForbidden()

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
@login_required
def field_delete(request, tournament_id, pk):
    field = get_object_or_404(Field, pk=pk, tournament_id=tournament_id)

    # Restrict unauthorized access
    if field.tournament.owner != request.user:
        return HttpResponseForbidden()

    if field.match_set.exists():
        return JsonResponse({'success': False, 'error': 'Cannot delete field with assigned matches.'})

    field.delete()
    return JsonResponse({'success': True})


@login_required
def generate_tournament_schedule(request, tournament_id):
    tournament = get_object_or_404(Tournament, pk=tournament_id)

    if request.method == 'POST':
        form = TournamentScheduleForm(request.POST)
        if form.is_valid():
            start_time_input = form.cleaned_data['start_time']
            game_duration_minutes = form.cleaned_data['game_duration']
            pause_duration_minutes = form.cleaned_data['pause_duration']

            # Build a full datetime object for today with the input time
            start_time = timezone.now().replace(
                hour=start_time_input.hour,
                minute=start_time_input.minute,
                second=0,
                microsecond=0
            )

            game_duration = timedelta(minutes=game_duration_minutes)
            pause_duration = timedelta(minutes=pause_duration_minutes)

            try:
                create_round_robin_matches(
                    tournament=tournament,
                    start_time=start_time,
                    game_duration=game_duration,
                    pause_duration=pause_duration
                )
                messages.success(request, "Round-robin schedule generated successfully!")
            except Exception as e:
                messages.error(request, f"Error generating schedule: {str(e)}")

            return redirect('tournament-detail', pk=tournament.pk)
    else:
        form = TournamentScheduleForm()

    return render(request, 'tournament/generate_schedule.html', {
        'form': form,
        'tournament': tournament
    })
