from django.contrib import messages
from django.db import transaction
from django.db.models import Q, F, Count, ExpressionWrapper, DateTimeField
from django.utils import timezone
from django.utils.timezone import localtime
from collections import defaultdict
from datetime import timedelta
from typing import List, Tuple
from .models import Team, Player, Tournament, Match, Field, MatchEvent
import json
from django.conf import settings
from pathlib import Path


def generate_round_robin(tournament: Tournament) -> List[List[Tuple[Team, Team]]]:
    """
    Generate round-robin match pairings for a tournament.
    
    Returns:
        rounds: List of rounds, each round is a list of (home_team, away_team) tuples
    """
    teams = list(tournament.teams.all())
    if not teams:
        return []

    # Handle odd number of teams by adding a "bye"
    bye_team = None
    if len(teams) % 2 == 1:
        bye_team = None
        teams.append(bye_team)

    n = len(teams)
    rounds = []

    for round_index in range(n - 1):
        round_matches = []
        for i in range(n // 2):
            home = teams[i]
            away = teams[n - 1 - i]
            # Skip matches with the "bye"
            if home is not None and away is not None:
                round_matches.append((home, away))
        rounds.append(round_matches)
        # Rotate teams (except first one)
        teams = [teams[0]] + [teams[-1]] + teams[1:-1]
    
    return rounds

def create_round_robin_matches(
    tournament,
    start_time,
    game_duration: timedelta,
    pause_duration: timedelta
):
    """
    Create Match objects for a tournament using round-robin pairings,
    distributing matches across available fields fairly so no team
    has consecutive matches without a break when multiple fields exist.

    game_duration already accounts for halves and half-time break if applicable
    — the caller is responsible for computing the total match duration.
    """
    with transaction.atomic():
        fields = list(tournament.fields.all())
        if not fields:
            raise ValueError("Tournament has no fields.")

        rounds = generate_round_robin(tournament)
        current_time = start_time
        slot_duration = game_duration + pause_duration

        matches_to_create = []

        for round_index, round_matches in enumerate(rounds, start=1):
            slots = [round_matches[i:i + len(fields)] for i in range(0, len(round_matches), len(fields))]

            for slot in slots:
                for i, (home, away) in enumerate(slot):
                    field = fields[i % len(fields)]
                    matches_to_create.append(
                        Match(
                            tournament=tournament,
                            home_team=home,
                            away_team=away,
                            start_time=current_time,
                            field=field
                        )
                    )
                current_time += slot_duration

    Match.objects.bulk_create(matches_to_create)

def propagate_match_delay(match, new_start_time):
    """
    Adjust the start time of `match` and all subsequent matches
    in the same tournament using a bulk update.
    """

    old_start_time = match.start_time
    delay = new_start_time - old_start_time

    if delay.total_seconds() == 0:
        return

    with transaction.atomic():
        # Update the delayed match
        match.start_time = new_start_time
        match.save(update_fields=["start_time"])

        # Shift future matches based on OLD time, excluding current match
        match.start_time = new_start_time
        match.save(update_fields=["start_time"])

        (
            match.tournament.matches
            .filter(start_time__gt=old_start_time)
            .exclude(pk=match.pk)
            .update(start_time=ExpressionWrapper(
                F("start_time") + delay,
                output_field=DateTimeField()
                )
            )
        )

def get_team_standings(tournament):
    """
    Returns a list of teams sorted by:
    1. Tournament points (DESC)
    2. Tie-breakers: goal difference among tied teams
    Fully optimized, avoids N+1.
    """

    teams = list(Team.objects.filter(tournament=tournament))
    points_groups = defaultdict(list)
    for team in teams:
        points_groups[team.tournament_points].append(team)

    # Prefetch finished matches
    matches = Match.objects.filter(
        tournament=tournament,
        is_finished=True
    ).select_related('home_team', 'away_team')

    # Prefetch goal events
    events = MatchEvent.objects.filter(
        match__in=matches,
        event_type='goal'
    ).select_related('team', 'match')

    # map: match_id -> list of events
    match_events_map = defaultdict(list)
    for event in events:
        match_events_map[event.match_id].append(event)

    sorted_teams = []

    for points in sorted(points_groups.keys(), reverse=True):
        group = points_groups[points]

        if len(group) == 1:
            group[0].goal_difference_vs_tied = 0  # set attribute for consistency
            sorted_teams.extend(group)
            continue

        # Tie-breaker
        for team in group:
            opponents = {t.id for t in group if t != team}
            goals_for = 0
            goals_against = 0

            for m in matches:  # use 'm' instead of 'match' to avoid shadowing
                if m.id not in match_events_map:
                    continue

                if {m.home_team_id, m.away_team_id} & opponents and team.id in (m.home_team_id, m.away_team_id):
                    for event in match_events_map[m.id]:
                        if event.team_id == team.id:
                            goals_for += 1
                        elif event.team_id in opponents:
                            goals_against += 1

            team.goal_difference_vs_tied = goals_for - goals_against

        group.sort(key=lambda t: (-t.goal_difference_vs_tied, t.name))
        sorted_teams.extend(group)

    return sorted_teams

def get_top_scorers(tournament, limit=5):
    """
    Returns the top scoring players in a tournament.
    Annotates each player with 'goal_count'.
    """

    top_players = Player.objects.filter(
        team__tournament=tournament
    ).annotate(
        goal_count=Count(
            'match_events',
            filter=Q(match_events__event_type='goal')
        )
    ).filter(
        goal_count__gt=0
    ).order_by('-goal_count')[:limit]

    return top_players

def build_timeline(tournament):
    """
    Builds a timeline structure for matches grouped by time and field.

    Returns:
        timeline: [
            {
                'time': 'HH:MM',
                'matches': [match_or_none, ...]
            },
            ...
        ]
        field_names: ordered list of field names
    """

    # Get all matches with related data
    matches = (
        tournament.matches
        .select_related('field', 'home_team', 'away_team')
        .order_by('start_time')
    )

    # Always derive fields from tournament (more stable than from matches)
    field_names = list(
        tournament.fields.order_by('name').values_list('name', flat=True)
    )

    # Initialize timeline structure
    timeline_dict = defaultdict(lambda: {field: None for field in field_names})

    for match in matches:
        time_str = localtime(match.start_time).strftime('%H:%M')
        timeline_dict[time_str][match.field.name] = match

    timeline = [
        {
            'time': time_str,
            'matches': [timeline_dict[time_str][field] for field in field_names],
        }
        for time_str in sorted(timeline_dict.keys())
    ]

    return timeline, field_names

def recalculate_match_points(match, new_home_score, new_away_score):
    """
    Recalculates tournament points for both teams based on a match result.

    - Reverses previous result if match was already finished
    - Applies new result
    - Updates team points atomically
    """

    home_team = match.home_team
    away_team = match.away_team

    with transaction.atomic():
        # Reverse previous result if match already finished
        if match.is_finished:
            if match.home_score > match.away_score:
                home_team.tournament_points = max(0, home_team.tournament_points - 3)
            elif match.home_score < match.away_score:
                away_team.tournament_points = max(0, away_team.tournament_points - 3)
            else:
                home_team.tournament_points = max(0, home_team.tournament_points - 1)
                away_team.tournament_points = max(0, away_team.tournament_points - 1)

        # Apply new result
        if new_home_score > new_away_score:
            home_team.tournament_points += 3
        elif new_home_score < new_away_score:
            away_team.tournament_points += 3
        else:
            home_team.tournament_points += 1
            away_team.tournament_points += 1

        home_team.save()
        away_team.save()

def reset_tournament_schedule(tournament):
    """
    Delete all matches (cascades to MatchEvent) and reset team points.
    """
    with transaction.atomic():
        tournament.matches.all().delete()
        tournament.teams.all().update(tournament_points=0)

def recalculate_points(match):
    tournament = match.tournament
    home = match.home_team.__class__.objects.get(pk=match.home_team.pk)
    away = match.away_team.__class__.objects.get(pk=match.away_team.pk)

    # reverse old points based on stored score
    if match.home_score > match.away_score:
        home.tournament_points = max(0, home.tournament_points - tournament.points_for_win)
        away.tournament_points = max(0, away.tournament_points - tournament.points_for_loss)
    elif match.away_score > match.home_score:
        away.tournament_points = max(0, away.tournament_points - tournament.points_for_win)
        home.tournament_points = max(0, home.tournament_points - tournament.points_for_loss)
    else:
        home.tournament_points = max(0, home.tournament_points - tournament.points_for_draw)
        away.tournament_points = max(0, away.tournament_points - tournament.points_for_draw)

    # recalculate new score from events
    home_goals = (
        match.events.filter(event_type='goal', team=home).count() +
        match.events.filter(event_type='own_goal', team=away).count()
    )
    away_goals = (
        match.events.filter(event_type='goal', team=away).count() +
        match.events.filter(event_type='own_goal', team=home).count()
    )

    # apply new points
    if home_goals > away_goals:
        home.tournament_points += tournament.points_for_win
        away.tournament_points += tournament.points_for_loss
    elif away_goals > home_goals:
        away.tournament_points += tournament.points_for_win
        home.tournament_points += tournament.points_for_loss
    else:
        home.tournament_points += tournament.points_for_draw
        away.tournament_points += tournament.points_for_draw

    home.save()
    away.save()

    match.home_score = home_goals
    match.away_score = away_goals
    match.save(update_fields=['home_score', 'away_score'])

def get_vite_asset(asset_name):
    manifest_path = Path(settings.BASE_DIR) / "tournamentapp/static//spa/.vite/manifest.json"

    with open(manifest_path) as f:
        manifest = json.load(f)

    return manifest[asset_name]