from django.contrib import messages
from .forms import TeamCreateForm
from .models import Team, Player

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
