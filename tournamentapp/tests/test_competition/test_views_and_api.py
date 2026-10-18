"""Organiser views and public API for Groups + Knockout."""
from datetime import date

import pytest
from django.urls import reverse

from tournamentapp.competition import refresh_knockout, schedule_groups_knockout
from tournamentapp.models import Match, MatchEvent, Player, Team, Tournament

from .conftest import GAME, PAUSE, START, TWO_GROUPS_OF_FIVE


@pytest.fixture
def scheduled(build_tournament):
    tournament = build_tournament(TWO_GROUPS_OF_FIVE, third_place_match=True)
    schedule_groups_knockout(tournament, START, GAME, PAUSE)
    return tournament


@pytest.fixture
def played(scheduled, play_group_stage):
    play_group_stage(scheduled)
    refresh_knockout(scheduled)
    return scheduled


def _semi(tournament, position=1):
    return Match.objects.get(tournament=tournament, stage=Match.STAGE_KNOCKOUT, round=4, bracket_position=position)


# ---------------------------------------------------------------------------
# Group setup page
# ---------------------------------------------------------------------------

@pytest.mark.django_db
def test_group_setup_page_owner_only(auth_client, client, other_user, tournament):
    url = reverse("group-setup", args=[tournament.pk])
    assert auth_client.get(url).status_code == 200

    client.force_login(other_user)
    assert client.get(url).status_code == 404


@pytest.mark.django_db
def test_group_setup_count_draw_and_assign(auth_client, tournament):
    teams = [Team.objects.create(name=f"T{i}", tournament=tournament) for i in range(4)]
    url = reverse("group-setup", args=[tournament.pk])

    auth_client.post(url, {"action": "set_count", "group_count": 2})
    assert tournament.groups.count() == 2

    auth_client.post(url, {"action": "random_draw"})
    assert not tournament.teams.filter(group__isnull=True).exists()

    group_a = tournament.groups.get(name="A")
    auth_client.post(url, {"action": "assign", **{f"team_{t.pk}": group_a.pk for t in teams}})
    assert group_a.teams.count() == 4


@pytest.mark.django_db
def test_group_setup_rejects_foreign_group(auth_client, tournament, other_user):
    team = Team.objects.create(name="T", tournament=tournament)
    other = Tournament.objects.create(name="Other", owner=other_user)
    foreign = other.groups.create(name="X")

    auth_client.post(reverse("group-setup", args=[tournament.pk]),
                     {"action": "assign", f"team_{team.pk}": foreign.pk})

    team.refresh_from_db()
    assert team.group is None


@pytest.mark.django_db
def test_group_setup_locked_after_schedule(client, scheduled, user):
    client.force_login(user)
    url = reverse("group-setup", args=[scheduled.pk])
    response = client.get(url)
    assert response.context["locked"] is True

    client.post(url, {"action": "set_count", "group_count": 4})
    assert scheduled.groups.count() == 2


# ---------------------------------------------------------------------------
# Schedule generation view
# ---------------------------------------------------------------------------

def _schedule_payload(**overrides):
    payload = {
        "start_date": "2026-06-20", "start_time": "10:00",
        "game_duration": 15, "pause_duration": 5, "break_before_knockout": 10,
    }
    payload.update(overrides)
    return payload


@pytest.mark.django_db
def test_generate_view_builds_groups_and_bracket(client, user, build_tournament):
    tournament = build_tournament(TWO_GROUPS_OF_FIVE)
    client.force_login(user)

    response = client.post(reverse("generate-tournament-schedule", args=[tournament.pk]), _schedule_payload())

    assert response.status_code == 302
    assert tournament.matches.filter(stage=Match.STAGE_GROUP).count() == 20
    assert tournament.matches.filter(stage=Match.STAGE_KNOCKOUT).count() == 3
    tournament.refresh_from_db()
    assert tournament.tournament_date == date(2026, 6, 20)


@pytest.mark.django_db
def test_generate_view_reports_setup_problems(client, user, build_tournament):
    tournament = build_tournament(TWO_GROUPS_OF_FIVE)
    Team.objects.create(name="No group", tournament=tournament)
    client.force_login(user)

    response = client.post(reverse("generate-tournament-schedule", args=[tournament.pk]),
                           _schedule_payload(), follow=True)

    assert not tournament.matches.exists()
    assert any("not assigned" in str(m) for m in response.context["messages"])


@pytest.mark.django_db
def test_generate_form_starts_from_tournament_date(auth_client, tournament):
    tournament.tournament_date = date(2026, 9, 5)
    tournament.save()
    response = auth_client.get(reverse("generate-tournament-schedule", args=[tournament.pk]))
    assert response.context["form"].initial["start_date"] == date(2026, 9, 5)


# ---------------------------------------------------------------------------
# Live match views
# ---------------------------------------------------------------------------

@pytest.mark.django_db
def test_pages_render_with_undecided_knockout_teams(client, user, scheduled):
    client.force_login(user)
    semi = _semi(scheduled)
    detail = client.get(reverse("tournament-detail", args=[scheduled.pk]))
    live = client.get(reverse("match-edit", args=[scheduled.pk, semi.pk]))
    board = client.get(reverse("leaderboard", args=[scheduled.pk]))

    assert detail.status_code == live.status_code == board.status_code == 200
    assert "Group winner #1" in detail.content.decode()
    assert "Group winner #1" in live.content.decode()
    assert "Semi-final" in board.content.decode()


@pytest.mark.django_db
def test_events_rejected_while_teams_undecided(client, user, scheduled):
    client.force_login(user)
    semi = _semi(scheduled)
    response = client.post(reverse("add-match-event", args=[scheduled.pk, semi.pk]), {
        "event_type": "goal", "team": "home", "team_id": 1, "player_id": 1,
    })
    assert response.status_code == 400


@pytest.mark.django_db
def test_finishing_last_group_match_fills_bracket(client, user, scheduled, play_group_stage):
    last = scheduled.matches.filter(stage=Match.STAGE_GROUP).order_by('-start_time').first()
    play_group_stage(scheduled, overrides={})
    last.is_finished = False
    last.save()
    client.force_login(user)

    client.post(reverse("finish-match", args=[scheduled.pk, last.pk]))

    assert _semi(scheduled).teams_known


@pytest.mark.django_db
def test_finish_view_requires_penalties_for_draw(client, user, played):
    client.force_login(user)
    semi = _semi(played)
    url = reverse("finish-match", args=[played.pk, semi.pk])

    client.post(url)                                   # 0-0, no penalties
    assert _semi(played).is_finished is False

    client.post(url, {"home_penalties": "5", "away_penalties": "4"})
    semi = _semi(played)
    assert semi.is_finished and semi.winner == semi.home_team
    assert semi.decided_by == Match.DECIDED_PENALTIES


@pytest.mark.django_db
def test_finish_view_rejects_bad_penalty_input(client, user, played):
    client.force_login(user)
    semi = _semi(played)
    client.post(reverse("finish-match", args=[played.pk, semi.pk]), {"home_penalties": "x", "away_penalties": "4"})
    assert _semi(played).is_finished is False


@pytest.mark.django_db
def test_manual_result_form_for_knockout(client, user, played):
    client.force_login(user)
    semi = _semi(played)
    url = reverse("match-edit", args=[played.pk, semi.pk])

    response = client.post(url, {"home_score": 1, "away_score": 1})
    assert response.status_code == 200 and _semi(played).is_finished is False

    response = client.post(url, {"home_score": 1, "away_score": 1, "home_penalties": 2, "away_penalties": 4})
    assert response.status_code == 302
    assert _semi(played).winner == _semi(played).away_team


@pytest.mark.django_db
def test_removing_goal_reopens_drawn_knockout_match(client, user, played):
    client.force_login(user)
    semi = _semi(played)
    player = Player.objects.create(name="Scorer", team=semi.home_team)
    goal = MatchEvent.objects.create(match=semi, team=semi.home_team, player=player, event_type='goal')
    client.post(reverse("finish-match", args=[played.pk, semi.pk]))
    assert _semi(played).is_finished

    response = client.delete(reverse("delete-match-event", args=[played.pk, goal.pk]))

    assert response.json()["is_finished"] is False
    assert _semi(played).winner is None


@pytest.mark.django_db
def test_slot_override_view(client, user, other_user, played):
    final = Match.objects.get(tournament=played, stage=Match.STAGE_KNOCKOUT, round=2, is_third_place=False)
    team = Team.objects.get(tournament=played, name="A5")
    url = reverse("set-knockout-slot", args=[played.pk, final.pk])

    client.force_login(other_user)
    assert client.post(url, {"side": "home", "team_id": team.pk}).status_code == 404

    client.force_login(user)
    client.post(url, {"side": "home", "team_id": team.pk})
    final.refresh_from_db()
    assert final.home_team == team and final.slots.get(side="home").is_manual_override


@pytest.mark.django_db
def test_knockout_matches_cannot_be_deleted(client, user, scheduled):
    client.force_login(user)
    semi = _semi(scheduled)
    client.post(reverse("delete-match", args=[scheduled.pk, semi.pk]))
    assert Match.objects.filter(pk=semi.pk).exists()


@pytest.mark.django_db
def test_tournament_settings_lock_format_after_schedule(client, user, scheduled):
    client.force_login(user)
    response = client.get(reverse("tournament-edit", args=[scheduled.pk]))
    assert response.context["form"].fields["format"].disabled
    assert response.context["form"].fields["qualifiers_per_group"].disabled


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

@pytest.mark.django_db
def test_schedule_api_labels_and_placeholders(client, scheduled):
    data = client.get(reverse("api-schedule", args=[scheduled.slug])).json()
    matches = [m for row in data["timeline"] for m in row["matches"] if m]

    group_match = next(m for m in matches if m["stage"] == "group")
    semi = next(m for m in matches if m["round_label"] == "Semi-final 1")
    assert group_match["group"] in ("A", "B") and group_match["round_label"].startswith("Group")
    assert semi["home_team"] == "Group winner #1" and semi["home_placeholder"] is True
    assert all("datetime" in row for row in data["timeline"])


@pytest.mark.django_db
def test_leaderboard_api_returns_group_tables(client, played):
    data = client.get(reverse("api-leaderboard", args=[played.slug])).json()

    assert data["format"] == "groups_knockout"
    assert data["standings"] == []
    assert [g["name"] for g in data["groups"]] == ["A", "B"]
    group_a = data["groups"][0]["standings"]
    assert [row["team_name"] for row in group_a][:2] == ["A1", "A2"]
    assert [row["qualifies"] for row in group_a] == [True, True, False, False, False]
    assert group_a[0]["points"] == 12 and group_a[0]["played"] == 4


@pytest.mark.django_db
def test_leaderboard_api_round_robin_keeps_single_table(client, tournament, team, match):
    data = client.get(reverse("api-leaderboard", args=[tournament.slug])).json()
    assert data["format"] == "round_robin"
    assert len(data["groups"]) == 1 and data["groups"][0]["name"] is None
    assert {row["team_name"] for row in data["standings"]} == {"Team A", "Team B"}


@pytest.mark.django_db
def test_bracket_api(client, played):
    from tournamentapp.competition import apply_knockout_result
    apply_knockout_result(_semi(played, 1), 3, 0)

    data = client.get(reverse("api-bracket", args=[played.slug])).json()

    assert [r["label"] for r in data["rounds"]] == ["Semi-final", "Final", "Third place"]
    final = data["rounds"][1]["matches"][0]
    assert final["home_team"] == "A1" and final["home_placeholder"] is False
    assert final["away_team"] == "Winner SF 2" and final["away_placeholder"] is True
    assert data["rounds"][0]["matches"][0]["winner"] == "A1"


@pytest.mark.django_db
def test_bracket_api_empty_for_round_robin(client, tournament):
    data = client.get(reverse("api-bracket", args=[tournament.slug])).json()
    assert data == {"format": "round_robin", "rounds": []}


@pytest.mark.django_db
def test_meta_api_exposes_format(client, scheduled):
    data = client.get(reverse("api-tournament-meta", args=[scheduled.slug])).json()
    assert data["format"] == "groups_knockout"


@pytest.mark.django_db
def test_organiser_pages_render_for_groups_tournament(client, user, played):
    client.force_login(user)
    semi = _semi(played)
    pages = {
        "dashboard": reverse("tournament-dashboard", args=[played.pk]),
        "groups": reverse("group-setup", args=[played.pk]),
        "generate": reverse("generate-tournament-schedule", args=[played.pk]),
        "edit": reverse("tournament-edit", args=[played.pk]),
        "live": reverse("match-edit", args=[played.pk, semi.pk]),
        "detail": reverse("match-detail", args=[played.pk, semi.pk]),
    }
    responses = {name: client.get(url) for name, url in pages.items()}

    assert {name: r.status_code for name, r in responses.items()} == {name: 200 for name in pages}
    assert "Manage Groups" in responses["dashboard"].content.decode()
    assert "Bracket of 4" in responses["groups"].content.decode()
    assert "Break Before Knockout" in responses["generate"].content.decode()
    live = responses["live"].content.decode()
    assert 'name="home_penalties"' in live and 'name="team_id"' in live


@pytest.mark.django_db
def test_flash_messages_are_shown(client, user, played):
    """base.html renders messages, so organisers see knockout conflicts."""
    client.force_login(user)
    semi = _semi(played)
    response = client.post(reverse("finish-match", args=[played.pk, semi.pk]), follow=True)
    assert "penalty shoot-out" in response.content.decode()
