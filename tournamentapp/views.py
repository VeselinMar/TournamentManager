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
from datetime import timedelta, datetime
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, get_object_or_404, render
from .models import Match, Team, GoalEvent, Player, MatchEvent, Field, Tournament
from .forms import TeamCreateForm, MatchCreateForm, MatchEditForm, MatchEventForm, FieldCreateForm, TournamentCreateForm,TournamentScheduleForm
from .mixins import TournamentOwnerMixin, TournamentAccessMixin
from django.urls import reverse_lazy, reverse
from django.db.models import Q, Count
from collections import defaultdict
from django.utils.timezone import localtime, datetime
from formtools.wizard.views import SessionWizardView
from .utils import create_round_robin_matches, propagate_match_delay, get_team_standings, get_top_scorers, build_timeline
from .services import handle_batch_lines


def about_view(request):
    return render(request, "footer/about.html")

def contact_view(request):
    return render(request, "footer/contact.html")

def privacy_policy_view(request):
    return render(request, "footer/privacy_policy.html")

class TournamentCreateView(LoginRequiredMixin, CreateView):
    model = Tournament
    form_class = TournamentCreateForm
    template_name = 'tournament/tournament_form.html'

    def dispatch(self, request, *args, **kwargs):
        existing = Tournament.objects.filter(owner=request.user).first()
        if existing:
            return redirect('tournament-detail', pk=existing.pk)
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        form.instance.owner = self.request.user
        
        response = super().form_valid(form)

        Field.objects.get_or_create(
            name="Main Field",
            tournament=self.object,
            defaults={"owner": self.object.owner}
        )

        return response

    def get_success_url(self):
        return reverse('team-create', kwargs={'tournament_id': self.object.pk})

class TournamentPublicView(DetailView):
    model = Tournament
    template_name = 'tournament/public_home.html'
    slug_field = 'slug'
    slug_url_kwarg = 'slug'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        tournament = self.object

        context["sponsors"] = tournament.sponsors.all()

        timeline, field_names = build_timeline(tournament)

        context.update({
            'timeline': timeline,
            'field_names': field_names
        })

        return context

class TournamentDetailView(LoginRequiredMixin, TournamentOwnerMixin, DetailView):
    model = Tournament
    template_name = 'tournament/tournament_detail.html'
    context_object_name = 'tournament'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        tournament = self.object

        timeline, field_names = build_timeline(tournament)

        context.update({
            'timeline': timeline,
            'field_names': field_names,
        })

        return context

class LandingPageView(TemplateView):
    template_name = 'tournament/landing_page.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['tournaments'] = Tournament.objects.filter(is_finished=False)
        return context

class TeamListView(LoginRequiredMixin, TournamentAccessMixin, ListView):
    model = Team
    template_name = 'teams/team_list.html'
    context_object_name = 'teams'

    def get_queryset(self):
        tournament = self.get_tournament()
        return Team.objects.filter(tournament=tournament).order_by('name')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['tournament'] = self.get_tournament
        return context

class TeamDetailView(LoginRequiredMixin, TournamentAccessMixin, DetailView):
    model = Team
    template_name = 'teams/team_detail.html'
    context_object_name = 'team'

    def get_object(self, queryset=None):
        tournament = self.get_tournament()
        team_pk = self.kwargs.get('pk')
        return get_object_or_404(Team, pk=team_pk, tournament=tournament)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        team = self.object
        tournament = team.tournament

        # Matches for the team
        all_matches = Match.objects.filter(
            Q(home_team=team) | Q(away_team=team)
        ).select_related('home_team', 'away_team', 'field').order_by('start_time')

        # Finished matches with results
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

        upcoming_matches = all_matches.filter(is_finished=False)

        context.update({
            'finished_matches': finish_match,
            'upcoming_matches': upcoming_matches,
            'players': team.players.all(),
            'tournament': tournament,
        })

        return context

class TeamCreateView(LoginRequiredMixin, TournamentAccessMixin, CreateView):
    model = Team
    form_class = TeamCreateForm
    template_name = 'teams/team_form.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        tournament = self.get_tournament()
        context['tournament'] = tournament
        context['teams'] = tournament.teams.all().prefetch_related('player_set')
        return context

    def get_success_url(self):
        return reverse('team-list', kwargs={'tournament_id': self.get_tournament.pk})

    def post(self, request, *args, **kwargs):
        submit_type = request.POST.get('submit_type')
        tournament = self.get_tournament()

        # ===========================
        # CSV batch upload
        # ===========================
        if submit_type == 'batch' and request.FILES.get('csv_file'):
            csv_file = request.FILES['csv_file']
            if not csv_file.name.lower().endswith('.csv'):
                messages.error(request, 'Please upload a valid CSV file.')
                return redirect('team-create', tournament_id=tournament.pk)

            try:
                decoded_lines = csv_file.read().decode('utf-8').splitlines()
                created_teams, created_players = handle_batch_lines(request, tournament, decoded_lines)
                messages.success(request, f'{created_teams} team(s) and {created_players} player(s) successfully created.')
            except Exception as e:
                messages.error(request, f'Some teams could not be created — they may already exist.')

            return redirect('team-create', tournament_id=tournament.pk)

        # ===========================
        # Multi-line textarea input
        # ===========================
        elif submit_type != 'batch':
            multiline_input = request.POST.get('name', '').splitlines()
            if not multiline_input:
                messages.error(request, 'Please enter at least one team.')
                return redirect('team-create', tournament_id=tournament.pk)

            created_teams, created_players = handle_batch_lines(request, tournament, multiline_input)
            messages.success(request, f'{created_teams} team(s) and {created_players} player(s) successfully created.')
            return redirect('team-create', tournament_id=tournament.pk)

        # ===========================
        # Fallback: default CreateView behavior
        # ===========================
        return super().post(request, *args, **kwargs)

class MatchCreateView(LoginRequiredMixin, TournamentAccessMixin, CreateView):
    model = Match
    form_class = MatchCreateForm
    template_name = 'matches/match_create.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        tournament = self.get_tournament()
        context['fields'] = Field.objects.filter(tournament=tournament)
        context['tournament'] = tournament
        return context
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['tournament'] = self.get_tournament()
        return kwargs

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        form.instance.tournament = self.get_tournament()
        return form
    

    def get_success_url(self):
        return reverse('tournament-detail', kwargs={'pk': self.get_tournament().pk})

class MatchDetailView(LoginRequiredMixin, TournamentAccessMixin, DetailView):
    model = Match
    template_name = 'matches/match_detail.html'
    context_object_name = 'match'

    def get_object(self, queryset=None):
        match = super().get_object(queryset)
        if match.tournament_id != self.get_tournament().pk:
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

class MatchEditView(LoginRequiredMixin, TournamentAccessMixin, UpdateView):
    model = Match
    form_class = MatchEditForm
    template_name = 'matches/match_edit.html'

    def get_object(self, queryset=None):
        match = super().get_object(queryset)
        tournament = self.get_tournament()

        if match.tournament_id != tournament.pk:
            raise Http404("Match does not belong to this tournament.")
        return match

    def form_valid(self, form):
        old_start_time = self.get_object().start_time
        response = super().form_valid(form)
        new_start_time = form.instance.start_time

        if new_start_time != old_start_time:
            propagate_match_delay(self.object, new_start_time)

        return response

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        match = self.object
        context.update({
            'match_events': match.events.all(),
            'tournament': self.get_tournament()
        })
        return context
        
class LeaderboardView(LoginRequiredMixin, TournamentAccessMixin, TemplateView):
    template_name = 'matches/leaderboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        tournament = self.get_tournament()

        context['players'] = get_top_scorers(tournament, limit=10)
        context['teams'] = get_team_standings(tournament)
        context['tournament'] = tournament
        return context
        
class FieldAddView(LoginRequiredMixin, TournamentAccessMixin, CreateView):
    model = Field
    form_class = FieldCreateForm
    template_name = 'fields/field_create.html'

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['tournament'] = self.get_tournament()
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        tournament = self.get_tournament()
        context['fields'] = Field.objects.filter(tournament=tournament)
        context['tournament'] = tournament
        return context

    def form_valid(self, form):
        tournament = self.get_tournament()
        form.instance.tournament = tournament
        form.instance.owner = self.request.user
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy('field-create', kwargs={'tournament_id': self.get_tournament().pk})

@require_POST
@login_required
def create_match_event(request, tournament_id, match_id):
    tournament = get_object_or_404(Tournament, id=tournament_id, owner=request.user)

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

    team = get_object_or_404(Team, id=team_id, tournament=tournament, owner=request.user)

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
    tournament = get_object_or_404(Tournament, id=tournament_id, owner=request.user)

    match = get_object_or_404(Match, id=match_id, tournament=tournament)

    if not match.is_finished:
        match.apply_result()

    return redirect('tournament-detail', pk=tournament_id)

@require_http_methods(['DELETE'])
@login_required
def remove_match_event(request, tournament_id, event_id):
    event = get_object_or_404(MatchEvent, id=event_id, owner=request.user)
    match = event.match

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
    field = get_object_or_404(Field, pk=pk, tournament_id=tournament_id, owner=request.user)

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
    field = get_object_or_404(Field, pk=pk, tournament_id=tournament_id, owner=request.user)

    if field.match_set.exists():
        return JsonResponse({'success': False, 'error': 'Cannot delete field with assigned matches.'})

    field.delete()
    return JsonResponse({'success': True})


@login_required
def generate_tournament_schedule(request, tournament_id):
    tournament = get_object_or_404(Tournament, pk=tournament_id, owner=request.user)

    if request.method == 'POST':
        form = TournamentScheduleForm(request.POST)
        if form.is_valid():
            start_date = form.cleaned_data['start_date']
            start_time_input = form.cleaned_data['start_time']
            pause_duration = timedelta(minutes=form.cleaned_data['pause_duration'])

            start_time = timezone.make_aware(
                datetime.combine(start_date, start_time_input)
            )

            if form.cleaned_data['has_halves']:
                half = timedelta(minutes=form.cleaned_data['half_duration'])
                half_break = timedelta(minutes=form.cleaned_data['half_time_break'])
                total_match_duration = (half * 2) + half_break
            else:
                total_match_duration = timedelta(minutes=form.cleaned_data['game_duration'])

            try:
                create_round_robin_matches(
                    tournament=tournament,
                    start_time=start_time,
                    game_duration=total_match_duration,
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