from django.contrib import messages
from django.db import transaction
from django.db.models import Q, F, Count, ExpressionWrapper, DateTimeField
from django.utils import timezone
from django.utils.timezone import localtime
from collections import defaultdict
from datetime import timedelta, datetime
from typing import List, Tuple, Optional
from .models import Team, Player, Tournament, Match, Field, MatchEvent
import json
import logging
import random
from django.conf import settings
from pathlib import Path

logger = logging.getLogger(__name__)

LOOKAHEAD_ATTEMPTS = 10  # number of random shuffles to try before inserting rest slot

def generate_round_robin(tournament: Tournament) -> List[Tuple[Team, Team]]:
    """
    Generate all round-robin pairings for a tournament as a flat list.

    The bye sentinel is fixed at the LAST position during rotation so it
    never occupies index 0, preserving a consistent fixed anchor.

    Home/away is balanced greedily: for each pair, the team with the lower
    net home count (home_games - away_games) is assigned as home. Ties go
    to the naturally ordered home candidate.

    Raises:
        ValueError: If the tournament has fewer than 2 teams.
    """
    teams = list(tournament.teams.all())

    if len(teams) < 2:
        raise ValueError(
            f"Tournament requires at least 2 teams, got {len(teams)}."
        )

    # Fix the bye at the end, not in the rotating pool, so it never
    # displaces the anchor at index 0.
    has_bye = len(teams) % 2 == 1
    if has_bye:
        teams.append(None)

    n = len(teams)
    # Separate anchor from rotating slice
    anchor = teams[0]
    rotating = teams[1:]  # length n-1, bye (if any) is at rotating[-1]

    net_home: dict[Team, int] = defaultdict(int)  # home_games - away_games
    all_matches: List[Tuple[Team, Team]] = []

    for _ in range(n - 1):
        round_teams = [anchor] + rotating
        for i in range(n // 2):
            home = round_teams[i]
            away = round_teams[n - 1 - i]

            if home is None or away is None:
                continue

            # Assign home to the team with the lower net home count.
            # On a tie, keep the natural (home, away) order.
            if net_home[away] < net_home[home]:
                home, away = away, home

            net_home[home] += 1
            net_home[away] -= 1
            all_matches.append((home, away))

        # Rotate only the non-anchor slice; bye stays at the tail naturally
        rotating = [rotating[-1]] + rotating[:-1]

    return all_matches


def _try_fill_slot(
    remaining: List[Tuple[Team, Team]],
    field_count: int,
    prev_slot_teams: set,
) -> Tuple[List[Tuple[Team, Team]], List[int]] | None:
    """
    Attempt to fill a slot of up to `field_count` matches from `remaining`,
    respecting the rest constraint against `prev_slot_teams`.

    Returns (slot_matches, used_indices) if at least one match was found,
    or None if no valid match exists at all.
    """
    slot: List[Tuple[Team, Team]] = []
    slot_teams: set = set()
    used_indices: List[int] = []

    for idx, (home, away) in enumerate(remaining):
        if len(slot) == field_count:
            break
        if home in prev_slot_teams or away in prev_slot_teams:
            continue
        if home in slot_teams or away in slot_teams:
            continue
        slot.append((home, away))
        slot_teams |= {home, away}
        used_indices.append(idx)

    if not slot:
        return None
    return slot, used_indices


def _assign_slots(
    matches: List[Tuple[Team, Team]],
    field_count: int,
) -> List[List[Tuple[Team, Team]]]:
    """
    Assign matches to slots of up to `field_count`, ensuring no team plays
    in consecutive slots.

    Uses lookahead: before inserting a forced rest slot, tries
    LOOKAHEAD_ATTEMPTS random orderings of the remaining matches to see if
    any avoids the deadlock. Inserts an empty rest slot only if all
    attempts fail.

    Returns:
        List of slots; empty lists are forced rest slots.
    """
    remaining = list(matches)
    slots: List[List[Tuple[Team, Team]]] = []
    prev_slot_teams: set = set()

    while remaining:
        result = _try_fill_slot(remaining, field_count, prev_slot_teams)

        if result is None:
            # Lookahead: try random permutations of remaining before giving up
            resolved = False
            for _ in range(LOOKAHEAD_ATTEMPTS):
                candidate = random.sample(remaining, len(remaining))
                result = _try_fill_slot(candidate, field_count, prev_slot_teams)
                if result is not None:
                    # Rebuild remaining in the order that worked
                    slot, used_indices = result
                    for idx in sorted(used_indices, reverse=True):
                        candidate.pop(idx)
                    remaining = candidate
                    slots.append(slot)
                    prev_slot_teams = {t for m in slot for t in m}
                    resolved = True
                    break

            if not resolved:
                logger.info(
                    "Inserting forced rest slot after slot %d to maintain "
                    "rest constraint.",
                    len(slots),
                )
                slots.append([])
                prev_slot_teams = set()
        else:
            slot, used_indices = result
            for idx in sorted(used_indices, reverse=True):
                remaining.pop(idx)
            slots.append(slot)
            prev_slot_teams = {t for m in slot for t in m}

    return slots


def create_round_robin_matches(
    tournament: Tournament,
    start_time: datetime,
    game_duration: timedelta,
    pause_duration: timedelta,
) -> None:
    """
    Create Match objects for a tournament using round-robin pairings,
    scheduled as compactly as possible while ensuring each team has at
    least one slot of rest between games.

    Under-full slots assign fields left-to-right; remaining fields are
    idle for that slot. Time is derived solely from slot index, so
    start_time + field uniquely identifies each match.

    Raises:
        TypeError:  If start_time is not a datetime.
        ValueError: If start_time is not timezone-aware, or the tournament
                    has no fields configured.
    """
    if not isinstance(start_time, datetime):
        raise TypeError(f"start_time must be a datetime, got {type(start_time)!r}.")
    if start_time.tzinfo is None:
        raise ValueError("start_time must be timezone-aware.")

    with transaction.atomic():
        fields = list(tournament.fields.all())
        if not fields:
            raise ValueError("Tournament has no fields.")

        all_matches = generate_round_robin(tournament)
        slots = _assign_slots(all_matches, field_count=len(fields))

        slot_duration = game_duration + pause_duration
        matches_to_create = []

        for slot_index, slot in enumerate(slots):
            slot_time = start_time + slot_index * slot_duration
            for field_index, (home, away) in enumerate(slot):
                # field_index is always < len(fields) because _assign_slots
                # caps slot size at field_count
                matches_to_create.append(
                    Match(
                        tournament=tournament,
                        home_team=home,
                        away_team=away,
                        start_time=slot_time,
                        field=fields[field_index],
                    )
                )

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

def _empty_stats():
    return {'played': 0, 'wins': 0, 'draws': 0, 'losses': 0,
            'goals_for': 0, 'goals_against': 0, 'points': 0}


def _accumulate(stats, team_id, goals_for, goals_against, points):
    row = stats[team_id]
    row['played'] += 1
    row['goals_for'] += goals_for
    row['goals_against'] += goals_against
    row['points'] += points
    if goals_for > goals_against:
        row['wins'] += 1
    elif goals_for == goals_against:
        row['draws'] += 1
    else:
        row['losses'] += 1


def _collect_stats(tournament, matches, team_ids=None):
    """
    Aggregate results from finished matches. Scores are taken from the
    stored match result, so own goals and manually entered scores count.
    If `team_ids` is given, only matches between those teams are used
    (head-to-head mini-table).
    """
    stats = defaultdict(_empty_stats)
    for m in matches:
        if team_ids is not None and not (m.home_team_id in team_ids and m.away_team_id in team_ids):
            continue
        home_pts, away_pts = match_points(tournament, m.home_score, m.away_score)
        _accumulate(stats, m.home_team_id, m.home_score, m.away_score, home_pts)
        _accumulate(stats, m.away_team_id, m.away_score, m.home_score, away_pts)
    return stats


def get_team_standings(tournament):
    """
    Return the tournament's teams in ranking order.

    Teams are ordered by tournament points. Teams level on points are
    separated according to `tournament.tiebreak_rule`:

    head_to_head (default, UEFA style):
        1. points in matches between the tied teams
        2. goal difference in those matches
        3. goals scored in those matches
        4. overall goal difference
        5. overall goals scored
    goal_difference (FIFA style):
        1. overall goal difference
        2. overall goals scored
        3-5. the head-to-head criteria above

    Team name is the final, deterministic fallback.

    Each returned team carries: played, wins, draws, losses, goals_for,
    goals_against, goal_difference and goal_difference_vs_tied.
    """
    teams = list(Team.objects.filter(tournament=tournament))
    matches = list(
        Match.objects.filter(tournament=tournament, is_finished=True)
        .only('home_team_id', 'away_team_id', 'home_score', 'away_score')
    )

    overall = _collect_stats(tournament, matches)
    for team in teams:
        row = overall[team.id]
        team.played = row['played']
        team.wins = row['wins']
        team.draws = row['draws']
        team.losses = row['losses']
        team.goals_for = row['goals_for']
        team.goals_against = row['goals_against']
        team.goal_difference = row['goals_for'] - row['goals_against']
        team.goal_difference_vs_tied = 0

    points_groups = defaultdict(list)
    for team in teams:
        points_groups[team.tournament_points].append(team)

    use_head_to_head_first = tournament.tiebreak_rule != Tournament.TIEBREAK_GOAL_DIFFERENCE
    sorted_teams = []

    for points in sorted(points_groups.keys(), reverse=True):
        group = points_groups[points]

        if len(group) > 1:
            tied_ids = {t.id for t in group}
            h2h = _collect_stats(tournament, matches, team_ids=tied_ids)
            for team in group:
                row = h2h[team.id]
                team.h2h_points = row['points']
                team.goal_difference_vs_tied = row['goals_for'] - row['goals_against']
                team.h2h_goals_for = row['goals_for']

        def sort_key(t):
            head_to_head = (
                -getattr(t, 'h2h_points', 0),
                -t.goal_difference_vs_tied,
                -getattr(t, 'h2h_goals_for', 0),
            )
            overall_record = (-t.goal_difference, -t.goals_for)
            primary, secondary = (
                (head_to_head, overall_record) if use_head_to_head_first
                else (overall_record, head_to_head)
            )
            return primary + secondary + (t.name.lower(),)

        group.sort(key=sort_key)
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

def match_points(tournament, home_goals, away_goals):
    """Return (home_points, away_points) for a result, using the tournament's point settings."""
    if home_goals > away_goals:
        return tournament.points_for_win, tournament.points_for_loss
    if away_goals > home_goals:
        return tournament.points_for_loss, tournament.points_for_win
    return tournament.points_for_draw, tournament.points_for_draw


def recalculate_match_points(match, new_home_score, new_away_score):
    """
    Apply a manually entered result to a match.

    - Reverses the previously stored result if the match was already finished
      (values are read from the database, not from the in-memory instance)
    - Applies the new result using the tournament's configured points
    - Marks the match as finished
    """
    tournament = match.tournament

    with transaction.atomic():
        stored = Match.objects.select_for_update().get(pk=match.pk)
        home = Team.objects.select_for_update().get(pk=stored.home_team_id)
        away = Team.objects.select_for_update().get(pk=stored.away_team_id)

        if stored.is_finished:
            old_home_pts, old_away_pts = match_points(tournament, stored.home_score, stored.away_score)
            home.tournament_points = max(0, home.tournament_points - old_home_pts)
            away.tournament_points = max(0, away.tournament_points - old_away_pts)

        new_home_pts, new_away_pts = match_points(tournament, new_home_score, new_away_score)
        home.tournament_points += new_home_pts
        away.tournament_points += new_away_pts
        home.save(update_fields=['tournament_points'])
        away.save(update_fields=['tournament_points'])

        stored.home_score = new_home_score
        stored.away_score = new_away_score
        stored.is_finished = True
        stored.save(update_fields=['home_score', 'away_score', 'is_finished'])

    return stored

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