from django.contrib import messages
from django.db import transaction
from datetime import timedelta
from django.utils import timezone
from typing import List, Tuple
from .forms import TeamCreateForm
from .models import Team, Player, Tournament, Match, Field

def handle_batch_lines(request, tournament, lines):
    """
    Process list of lines (from CSV or multi-line textarea) to create teams and players.

    Args:
        request: Django request object (for messages)
        tournament: Tournament instance to assign teams to
        lines: list of strings (lines from CSV or textarea)

    Returns:
        created_teams, created_players: integers
    """
    created_teams = 0
    created_players = 0
    current_team = None

    for line in lines:
        line = line.strip()
        if not line:
            continue

        # New team
        if line[0].isupper():
            form = TeamCreateForm(data={'name': line})
            if form.is_valid():
                team = form.save(commit=False)
                team.tournament = tournament
                team.save()
                current_team = team
                created_teams += 1
            else:
                messages.warning(
                    request,
                    f"Skipped invalid team '{line}': {form.errors.get('name', ['Invalid data'])[0]}"
                )

        # Player line (starts with '-')
        elif line.startswith('-') and current_team:
            player_name = line[1:].strip()
            if player_name:
                player, created = Player.objects.get_or_create(name=player_name, team=current_team)
                if created:
                    created_players += 1
            else:
                messages.warning(request, f"Skipped empty player name for team: {current_team}")
        else:
            messages.warning(request, f"Skipped unrecognizable line or no current team")

    return created_teams, created_players


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
    """
    fields = list(tournament.fields.all())
    if not fields:
        raise ValueError("Tournament has no fields.")

    rounds = generate_round_robin(tournament)
    current_time = start_time

    for round_index, round_matches in enumerate(rounds, start=1):
        # Split round matches into time slots based on number of fields
        slots = [round_matches[i:i + len(fields)] for i in range(0, len(round_matches), len(fields))]

        for slot in slots:
            # Assign matches to fields in order
            for i, (home, away) in enumerate(slot):
                field = fields[i % len(fields)]
                Match.objects.create(
                    tournament=tournament,
                    home_team=home,
                    away_team=away,
                    start_time=current_time,
                    field=field
                )
            # Increment time after all fields in this slot are used
            current_time += game_duration + pause_duration

def propagate_match_delay(match, new_start_time):
    """
    Adjust the start time of `match` and all subsequent matches in the same tournament.
    
    Args:
        match (Match): The match instance that was delayed.
        new_start_time (datetime): The new start time for the match.
    """
    delay = new_start_time - match.start_time
    if delay.total_seconds() == 0:
        # No delay, nothing to do
        return

    with transaction.atomic():
        # Update the delayed match
        match.start_time = new_start_time
        match.save()

        # Update all future matches in order
        future_matches = match.tournament.matches.filter(
            start_time__gt=match.start_time
        ).order_by('start_time')

        for m in future_matches:
            m.start_time += delay
            m.save()