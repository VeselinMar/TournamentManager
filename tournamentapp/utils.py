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
from .cache import batched_invalidation, invalidate


logger = logging.getLogger(__name__)

LOOKAHEAD_ATTEMPTS = 10  # number of random shuffles to try before inserting rest slot

def round_robin_rounds(teams: List[Team]) -> List[List[Tuple[Team, Team]]]:
    """
    Round-robin pairings grouped by round (circle method).

    The bye sentinel is fixed at the LAST position during rotation so it
    never occupies index 0, preserving a consistent fixed anchor.

    Home/away is balanced greedily: for each pair, the team with the lower
    net home count (home_games - away_games) is assigned as home. Ties go
    to the naturally ordered home candidate.
    """
    teams = list(teams)
    if len(teams) < 2:
        raise ValueError(
            f"Tournament requires at least 2 teams, got {len(teams)}."
        )

    if len(teams) % 2 == 1:
        teams.append(None)

    n = len(teams)
    anchor = teams[0]
    rotating = teams[1:]  # bye (if any) is at rotating[-1]

    net_home: dict = defaultdict(int)  # home_games - away_games
    rounds: List[List[Tuple[Team, Team]]] = []

    for _ in range(n - 1):
        round_teams = [anchor] + rotating
        round_matches = []
        for i in range(n // 2):
            home = round_teams[i]
            away = round_teams[n - 1 - i]

            if home is None or away is None:
                continue

            if net_home[away] < net_home[home]:
                home, away = away, home

            net_home[home] += 1
            net_home[away] -= 1
            round_matches.append((home, away))
        rounds.append(round_matches)

        # Rotate only the non-anchor slice; bye stays at the tail naturally
        rotating = [rotating[-1]] + rotating[:-1]

    return rounds


def generate_round_robin(tournament: Tournament) -> List[Tuple[Team, Team]]:
    """
    Generate all round-robin pairings for a tournament as a flat list.

    Raises:
        ValueError: If the tournament has fewer than 2 teams.
    """
    rounds = round_robin_rounds(tournament.teams.all())
    return [pair for round_matches in rounds for pair in round_matches]


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

    for idx, item in enumerate(remaining):
        home, away = item[0], item[1]
        if len(slot) == field_count:
            break
        if home in prev_slot_teams or away in prev_slot_teams:
            continue
        if home in slot_teams or away in slot_teams:
            continue
        slot.append(item)
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
                    prev_slot_teams = {t for m in slot for t in m[:2]}
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
            prev_slot_teams = {t for m in slot for t in m[:2]}

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

    with transaction.atomic(), batched_invalidation():
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
        invalidate(tournament.pk)  # bulk_create sends no signals

def propagate_match_delay(match, new_start_time):
    """
    Adjust the start time of `match` and all subsequent matches
    in the same tournament using a bulk update.
    """

    old_start_time = match.start_time
    delay = new_start_time - old_start_time

    if delay.total_seconds() == 0:
        return

    with transaction.atomic(), batched_invalidation():
        # Update the delayed match
        match.start_time = new_start_time
        match.save(update_fields=["start_time"])

        # Shift future matches based on OLD time, excluding current match
        invalidate(match.tournament_id)  # QuerySet.update sends no signals

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


def get_team_standings(tournament, group=None):
    """
    Return teams in ranking order with their record attached.

    Points are calculated from finished group-stage matches (nothing is
    stored on the team). For a Groups + Knockout tournament pass `group`
    to get that group's table; knockout matches never add points.

    Teams level on points are separated according to
    `tournament.tiebreak_rule`:

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

    Each returned team carries: points, played, wins, draws, losses,
    goals_for, goals_against, goal_difference and goal_difference_vs_tied.
    `tournament_points` is set to the same value as `points` for templates
    and code written before points were derived.
    """
    teams_qs = Team.objects.filter(tournament=tournament)
    matches_qs = Match.objects.filter(
        tournament=tournament, stage=Match.STAGE_GROUP, is_finished=True,
    )
    if group is not None:
        teams_qs = teams_qs.filter(group=group)
        matches_qs = matches_qs.filter(group=group)

    teams = list(teams_qs)
    matches = list(matches_qs.only('home_team_id', 'away_team_id', 'home_score', 'away_score'))

    overall = _collect_stats(tournament, matches)
    for team in teams:
        row = overall[team.id]
        team.points = row['points']
        team.tournament_points = row['points']
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
        points_groups[team.points].append(team)

    use_head_to_head_first = tournament.tiebreak_rule != Tournament.TIEBREAK_GOAL_DIFFERENCE
    sorted_teams = []

    for points in sorted(points_groups.keys(), reverse=True):
        tied = points_groups[points]

        if len(tied) > 1:
            tied_ids = {t.id for t in tied}
            h2h = _collect_stats(tournament, matches, team_ids=tied_ids)
            for team in tied:
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

        tied.sort(key=sort_key)
        sorted_teams.extend(tied)

    return sorted_teams


def get_group_tables(tournament):
    """[(group, standings)] for every group; a round robin has one table with group None."""
    if not tournament.uses_groups:
        return [(None, get_team_standings(tournament))]
    return [(g, get_team_standings(tournament, group=g)) for g in tournament.groups.all()]

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
        .select_related('field', 'home_team', 'away_team', 'group')
        .prefetch_related('slots')
        .order_by('start_time')
    )

    # Always derive fields from tournament (more stable than from matches)
    field_names = list(
        tournament.fields.order_by('name').values_list('name', flat=True)
    )

    # Initialize timeline structure
    timeline_dict = defaultdict(lambda: {field: None for field in field_names})

    # Rows are keyed by the full date and time (not just HH:MM), so matches
    # on different days can never overwrite each other.
    for match in matches:
        moment = localtime(match.start_time).replace(second=0, microsecond=0)
        timeline_dict[moment][match.field.name] = match

    timeline = [
        {
            'time': moment.strftime('%H:%M'),
            'datetime': moment,
            'matches': [timeline_dict[moment][field] for field in field_names],
        }
        for moment in sorted(timeline_dict.keys())
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
    Apply a manually entered group-stage result and mark the match finished.
    Standings are derived from match results, so only the match is updated.
    """
    with transaction.atomic():
        stored = Match.objects.select_for_update().get(pk=match.pk)
        stored.home_score = new_home_score
        stored.away_score = new_away_score
        stored.is_finished = True
        stored.save(update_fields=['home_score', 'away_score', 'is_finished'])
    return stored

def reset_tournament_schedule(tournament):
    """
    Delete all matches (cascades to events and knockout slots).
    Standings are derived from matches, so nothing else needs resetting.
    """
    with transaction.atomic(), batched_invalidation():
        tournament.matches.all().delete()
        invalidate(tournament.pk)

def recalculate_points(match):
    """
    Refresh the stored score of a finished match after its events changed.
    Knockout matches also get their winner re-evaluated.
    """
    from .competition import refresh_match_result
    refresh_match_result(match)

def get_vite_asset(asset_name):
    manifest_path = Path(settings.BASE_DIR) / "tournamentapp/static//spa/.vite/manifest.json"

    with open(manifest_path) as f:
        manifest = json.load(f)

    return manifest[asset_name]