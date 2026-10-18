"""
Groups + Knockout engine.

Flow
----
1. Groups are created and teams assigned (manually or by random draw).
2. `schedule_groups_knockout` creates all group matches and the full bracket.
   Knockout matches get their time and field immediately; their teams are
   described by `MatchSlot` rows (seed / winner of / loser of).
3. While the tournament runs, `refresh_knockout` fills in teams:
   seeds once the whole group stage is finished, winners/losers as knockout
   matches finish. Matches that already started are never changed silently;
   the mismatch is reported as a conflict instead.

Seeding
-------
Qualifiers = top `qualifiers_per_group` of every group plus the
`best_placed_qualifiers` best teams in the next position. They are seeded
by group position first (all group winners, then runners-up, ...), and
within a position by their record compared across groups (points, goal
difference and goals scored per game, so groups of different sizes are
compared fairly). The bracket has the next power-of-two size; missing
places become byes for the top seeds. First-round pairings between teams
from the same group are avoided where an equal-tier swap allows it.
"""
import math
import random
from dataclasses import dataclass, field as dc_field
from datetime import timedelta
from fractions import Fraction
from string import ascii_uppercase
from typing import List, Optional

from django.db import transaction
from django.db.models import Max

from .models import Group, Match, MatchEvent, MatchSlot, Team, Tournament


class CompetitionError(ValueError):
    """A user-facing problem with the tournament setup or a result."""


# ---------------------------------------------------------------------------
# Naming
# ---------------------------------------------------------------------------

_ROUND_NAMES = {2: 'Final', 4: 'Semi-final', 8: 'Quarter-final'}
_ROUND_ABBREVIATIONS = {2: 'F', 4: 'SF', 8: 'QF'}


def round_name(size, third_place=False):
    if third_place:
        return 'Third place'
    return _ROUND_NAMES.get(size, f'Round of {size}')


def _round_abbrev(size):
    return _ROUND_ABBREVIATIONS.get(size, f'R{size}')


def _ordinal(n):
    if 10 <= n % 100 <= 20:
        suffix = 'th'
    else:
        suffix = {1: 'st', 2: 'nd', 3: 'rd'}.get(n % 10, 'th')
    return f'{n}{suffix}'


def _match_short_name(size, position, third_place=False):
    if third_place:
        return 'Third place match'
    if size == 2:
        return 'Final'
    return f'{_round_abbrev(size)} {position}'


# ---------------------------------------------------------------------------
# Groups and draw
# ---------------------------------------------------------------------------

def _ensure_no_schedule(tournament):
    if tournament.matches.exists():
        raise CompetitionError("Reset the schedule before changing groups.")


def set_group_count(tournament, count):
    """Create or remove groups so the tournament has `count` groups (A, B, ...)."""
    if count < 1 or count > len(ascii_uppercase):
        raise CompetitionError(f"Number of groups must be between 1 and {len(ascii_uppercase)}.")
    _ensure_no_schedule(tournament)

    with transaction.atomic():
        existing = list(tournament.groups.order_by('order', 'name'))
        for extra in existing[count:]:
            extra.teams.update(group=None)
            extra.delete()
        for index in range(len(existing), count):
            Group.objects.create(tournament=tournament, name=ascii_uppercase[index], order=index)
    return list(tournament.groups.all())


def random_draw(tournament, rng=None):
    """Shuffle all teams into the existing groups as evenly as possible."""
    _ensure_no_schedule(tournament)
    groups = list(tournament.groups.all())
    if not groups:
        raise CompetitionError("Create groups before drawing teams.")

    rng = rng or random.SystemRandom()
    teams = list(tournament.teams.all())
    rng.shuffle(teams)
    with transaction.atomic():
        for index, team in enumerate(teams):
            team.group = groups[index % len(groups)]
            team.save(update_fields=['group'])
    return teams


def assign_team(team, group):
    _ensure_no_schedule(team.tournament)
    if group is not None and group.tournament_id != team.tournament_id:
        raise CompetitionError("Group belongs to another tournament.")
    team.group = group
    team.save(update_fields=['group'])


# ---------------------------------------------------------------------------
# Qualification plan
# ---------------------------------------------------------------------------

@dataclass
class QualifierPlan:
    groups: List[Group]
    group_sizes: List[int]
    per_group: int
    best_placed: int
    total: int
    bracket_size: int
    byes: int
    seed_labels: List[str] = dc_field(default_factory=list)

    @property
    def group_count(self):
        return len(self.groups)


def qualifier_plan(tournament):
    """Validate the group setup and describe the knockout bracket it produces."""
    groups = list(tournament.groups.all())
    if not groups:
        raise CompetitionError("Create at least one group and assign the teams.")

    unassigned = tournament.teams.filter(group__isnull=True).count()
    if unassigned:
        raise CompetitionError(f"{unassigned} team(s) are not assigned to a group.")

    sizes = [g.teams.count() for g in groups]
    if min(sizes) < 2:
        raise CompetitionError("Every group needs at least 2 teams.")

    per_group = tournament.qualifiers_per_group
    if per_group < 1:
        raise CompetitionError("At least one team per group must qualify.")
    if per_group > min(sizes):
        raise CompetitionError(
            f"{per_group} qualifiers per group, but the smallest group has only {min(sizes)} teams."
        )

    best_placed = tournament.best_placed_qualifiers
    groups_with_next_place = sum(1 for size in sizes if size > per_group)
    if best_placed > groups_with_next_place:
        raise CompetitionError(
            f"Only {groups_with_next_place} group(s) have a {_ordinal(per_group + 1)}-placed team, "
            f"so at most {groups_with_next_place} best-placed qualifier(s) are possible."
        )

    total = len(groups) * per_group + best_placed
    if total < 2:
        raise CompetitionError("At least 2 teams must qualify for the knockout stage.")

    bracket_size = 1 << math.ceil(math.log2(total))
    plan = QualifierPlan(
        groups=groups,
        group_sizes=sizes,
        per_group=per_group,
        best_placed=best_placed,
        total=total,
        bracket_size=bracket_size,
        byes=bracket_size - total,
    )
    plan.seed_labels = [_seed_label(plan, seed) for seed in range(1, total + 1)]
    return plan


def _seed_tier(plan, seed):
    """(group position, rank within that position) for a 1-based seed."""
    direct = plan.group_count * plan.per_group
    if seed <= direct:
        return (seed - 1) // plan.group_count + 1, (seed - 1) % plan.group_count + 1
    return plan.per_group + 1, seed - direct


def _seed_label(plan, seed):
    position, rank = _seed_tier(plan, seed)
    if plan.group_count == 1:
        return f"{_ordinal(position)} place"
    if position > plan.per_group:
        return f"Best {_ordinal(position)}-placed #{rank}"
    if position == 1:
        return f"Group winner #{rank}"
    if position == 2:
        return f"Runner-up #{rank}"
    return f"{_ordinal(position)} place #{rank}"


# ---------------------------------------------------------------------------
# Bracket structure
# ---------------------------------------------------------------------------

def bracket_order(size):
    """Standard seed positions, e.g. 8 -> [1, 8, 4, 5, 2, 7, 3, 6].
    Consecutive pairs meet in round one; seeds 1 and 2 can only meet in the final."""
    order = [1]
    n = 1
    while n < size:
        n *= 2
        order = [x for seed in order for x in (seed, n + 1 - seed)]
    return order


@dataclass
class _MatchSpec:
    round: int
    position: int
    home: tuple          # ('seed', n) | ('winner', spec) | ('loser', spec)
    away: tuple
    third_place: bool = False
    slot_index: Optional[int] = None
    field_index: Optional[int] = None
    instance: Optional[Match] = None


def _build_bracket(plan, with_third_place):
    """Return knockout match specs, earliest round first."""
    order = bracket_order(plan.bracket_size)
    entries = []          # what advances from each first-round pairing
    specs = []
    first_round = plan.bracket_size
    position = 0
    for i in range(0, len(order), 2):
        a, b = order[i], order[i + 1]
        if b > plan.total:              # bye: the higher seed goes straight through
            entries.append(('seed', a))
            continue
        position += 1
        spec = _MatchSpec(round=first_round, position=position, home=('seed', a), away=('seed', b))
        specs.append(spec)
        entries.append(('winner', spec))

    size = first_round // 2
    while len(entries) > 1:
        next_entries = []
        for i in range(0, len(entries), 2):
            spec = _MatchSpec(round=size, position=i // 2 + 1, home=entries[i], away=entries[i + 1])
            specs.append(spec)
            next_entries.append(('winner', spec))
        entries = next_entries
        size //= 2

    final = specs[-1]
    if with_third_place and final.home[0] == 'winner' and final.away[0] == 'winner':
        specs.append(_MatchSpec(
            round=2, position=1,
            home=('loser', final.home[1]), away=('loser', final.away[1]),
            third_place=True,
        ))
    return specs


def _source_placeholder(plan, source):
    kind, value = source
    if kind == 'seed':
        return plan.seed_labels[value - 1]
    spec = value
    name = _match_short_name(spec.round, spec.position, spec.third_place)
    return f"{'Winner' if kind == 'winner' else 'Loser'} {name}"


# ---------------------------------------------------------------------------
# Scheduling
# ---------------------------------------------------------------------------

def knockout_slot_duration(tournament, game_duration, pause_duration):
    duration = game_duration + pause_duration
    if tournament.allows_extra_time:
        duration += timedelta(minutes=tournament.extra_time_duration)
    return duration


def schedule_groups_knockout(tournament, start_time, game_duration, pause_duration,
                             break_before_knockout=timedelta(0)):
    """
    Create every group match and the complete knockout bracket.

    Group matches of all groups are interleaved by matchday and share the
    fields; no team plays in two consecutive slots. Knockout matches are
    placed after the group stage: a match is never scheduled in the slot
    directly after a match (or the group stage) that decides one of its
    teams, so every team gets at least one slot of rest. The final is on the
    first field; a third-place match runs next to it when a second field is
    available, otherwise right before it.

    Returns the list of created matches.
    """
    from .utils import _assign_slots, round_robin_rounds

    if start_time.tzinfo is None:
        raise CompetitionError("Start time must be timezone-aware.")
    if tournament.matches.exists():
        raise CompetitionError("This tournament already has a schedule. Reset it first.")

    fields = list(tournament.fields.order_by('pk'))
    if not fields:
        raise CompetitionError("Add at least one field before generating the schedule.")

    plan = qualifier_plan(tournament)
    group_slot = game_duration + pause_duration
    ko_slot = knockout_slot_duration(tournament, game_duration, pause_duration)

    with transaction.atomic():
        # ---- group stage
        rounds_by_group = [
            (group, round_robin_rounds(group.teams.order_by('pk')))
            for group in plan.groups
        ]
        items = []
        max_rounds = max(len(rounds) for _, rounds in rounds_by_group)
        for matchday in range(max_rounds):
            for group, rounds in rounds_by_group:
                if matchday < len(rounds):
                    for home, away in rounds[matchday]:
                        items.append((home, away, group, matchday + 1))

        slots = _assign_slots(items, field_count=len(fields))
        created = []
        for slot_index, slot in enumerate(slots):
            for field_index, (home, away, group, matchday) in enumerate(slot):
                created.append(Match(
                    tournament=tournament,
                    stage=Match.STAGE_GROUP,
                    group=group,
                    round=matchday,
                    home_team=home,
                    away_team=away,
                    start_time=start_time + slot_index * group_slot,
                    field=fields[field_index],
                ))
        Match.objects.bulk_create(created)

        last_group_slot = len(slots) - 1
        knockout_base = start_time + (last_group_slot + 1) * group_slot + break_before_knockout

        # ---- knockout stage
        specs = _build_bracket(plan, tournament.third_place_match)
        _place_knockout(specs, last_group_slot, len(fields))

        for spec in specs:
            match = Match.objects.create(
                tournament=tournament,
                stage=Match.STAGE_KNOCKOUT,
                round=spec.round,
                bracket_position=spec.position,
                is_third_place=spec.third_place,
                start_time=knockout_base + (spec.slot_index - (last_group_slot + 1)) * ko_slot,
                field=fields[spec.field_index],
            )
            spec.instance = match
            for side, source in (('home', spec.home), ('away', spec.away)):
                kind, value = source
                MatchSlot.objects.create(
                    match=match,
                    side=side,
                    source_type={
                        'seed': MatchSlot.SOURCE_SEED,
                        'winner': MatchSlot.SOURCE_WINNER,
                        'loser': MatchSlot.SOURCE_LOSER,
                    }[kind],
                    seed=value if kind == 'seed' else None,
                    source_match=None if kind == 'seed' else value.instance,
                    placeholder=_source_placeholder(plan, source),
                )
            created.append(match)

    return created


def _place_knockout(specs, last_group_slot, field_count):
    """Assign slot and field indexes to knockout specs (see schedule_groups_knockout)."""
    occupancy = {}

    final_round = [s for s in specs if s.round == 2]
    others = [s for s in specs if s.round != 2]
    if field_count > 1:
        final_round.sort(key=lambda s: s.third_place)          # final first -> field 0
    else:
        final_round.sort(key=lambda s: not s.third_place)      # third place first, final last

    for spec in others + final_round:
        earliest = 0
        for kind, value in (spec.home, spec.away):
            source_slot = last_group_slot if kind == 'seed' else value.slot_index
            earliest = max(earliest, source_slot + 2)
        slot = earliest
        while occupancy.get(slot, 0) >= field_count:
            slot += 1
        spec.slot_index = slot
        spec.field_index = occupancy.get(slot, 0)
        occupancy[slot] = spec.field_index + 1


# ---------------------------------------------------------------------------
# Seeding
# ---------------------------------------------------------------------------

def group_stage_complete(tournament):
    group_matches = tournament.matches.filter(stage=Match.STAGE_GROUP)
    return group_matches.exists() and not group_matches.filter(is_finished=False).exists()


def _cross_group_key(team):
    played = team.played or 1
    return (
        -Fraction(team.points, played),
        -Fraction(team.goal_difference, played),
        -Fraction(team.goals_for, played),
        team.name.lower(),
    )


def compute_seeds(tournament, plan=None):
    """Ordered list of qualified teams (index 0 = seed 1)."""
    from .utils import get_team_standings

    plan = plan or qualifier_plan(tournament)
    tables = [get_team_standings(tournament, group=g) for g in plan.groups]

    seeds = []
    for position in range(1, plan.per_group + 1):
        at_position = [table[position - 1] for table in tables if len(table) >= position]
        seeds.extend(sorted(at_position, key=_cross_group_key))

    if plan.best_placed:
        next_position = plan.per_group + 1
        at_position = [table[next_position - 1] for table in tables if len(table) >= next_position]
        seeds.extend(sorted(at_position, key=_cross_group_key)[:plan.best_placed])

    _avoid_same_group_pairings(plan, seeds)
    return seeds


def _avoid_same_group_pairings(plan, seeds):
    """Swap equal-tier seeds so first-round opponents come from different groups where possible."""
    if plan.group_count < 2:
        return
    order = bracket_order(plan.bracket_size)
    pairs = [
        (order[i], order[i + 1])
        for i in range(0, len(order), 2)
        if order[i + 1] <= plan.total
    ]

    def team(seed):
        return seeds[seed - 1]

    def clash(a, b):
        return team(a).group_id == team(b).group_id

    for a, b in pairs:
        if not clash(a, b):
            continue
        for c, d in pairs:
            if (c, d) == (a, b) or _seed_tier(plan, d)[0] != _seed_tier(plan, b)[0]:
                continue
            seeds[b - 1], seeds[d - 1] = seeds[d - 1], seeds[b - 1]
            if not clash(a, b) and not clash(c, d):
                break
            seeds[b - 1], seeds[d - 1] = seeds[d - 1], seeds[b - 1]


# ---------------------------------------------------------------------------
# Results and progression
# ---------------------------------------------------------------------------

def _loser(match):
    if not match.is_finished or match.winner_id is None:
        return None
    return match.away_team if match.winner_id == match.home_team_id else match.home_team


def refresh_knockout(tournament):
    """
    Fill knockout teams from the current results.

    Returns a list of human-readable conflicts for matches that already
    started but would now get a different team. Those matches are left
    unchanged for the organiser to correct (manual override).
    """
    if not tournament.uses_groups:
        return []

    knockout = list(
        tournament.matches.filter(stage=Match.STAGE_KNOCKOUT)
        .select_related('home_team', 'away_team', 'winner')
        .prefetch_related('slots')
        .order_by('-round', 'is_third_place', 'bracket_position')
    )
    if not knockout:
        return []

    seeds = None
    if group_stage_complete(tournament):
        seeds = compute_seeds(tournament)

    started_ids = set(
        MatchEvent.objects.filter(match__in=knockout).values_list('match_id', flat=True)
    )
    by_pk = {m.pk: m for m in knockout}
    conflicts = []

    for match in knockout:
        changed = []
        for slot in match.slots.all():
            if slot.is_manual_override:
                continue
            if slot.source_type == MatchSlot.SOURCE_SEED:
                desired = seeds[slot.seed - 1] if seeds else None
            else:
                source = by_pk[slot.source_match_id]
                if slot.source_type == MatchSlot.SOURCE_WINNER:
                    desired = source.winner if source.is_finished else None
                else:
                    desired = _loser(source)

            attr = 'home_team' if slot.side == MatchSlot.HOME else 'away_team'
            current = getattr(match, attr)
            if (current.pk if current else None) == (desired.pk if desired else None):
                continue

            if match.is_finished or match.pk in started_ids:
                conflicts.append(
                    f"{match.round_label}: {slot.side} team should now be "
                    f"{desired.name if desired else 'undecided'} "
                    f"(currently {current.name if current else 'empty'}). "
                    f"The match already started, so it was not changed — set the team manually if needed."
                )
                continue
            setattr(match, attr, desired)
            changed.append(f'{attr}_id')

        if changed:
            match.save(update_fields=changed)

    return conflicts


def apply_knockout_result(match, home_score, away_score, home_penalties=None,
                          away_penalties=None, extra_time=False):
    """
    Finish (or correct) a knockout match with the given score.

    Draws need a penalty result. Extra time is only allowed when the
    tournament plays it. Returns conflicts reported by `refresh_knockout`.
    """
    tournament = match.tournament
    if not match.is_knockout:
        raise CompetitionError("Only knockout matches have a winner.")
    if not match.teams_known:
        raise CompetitionError("Both teams must be known before the match can be finished.")
    if extra_time and not tournament.allows_extra_time:
        raise CompetitionError("This tournament goes straight to penalties; extra time is disabled.")

    has_penalties = home_penalties is not None or away_penalties is not None
    if home_score != away_score:
        if has_penalties:
            raise CompetitionError("Penalties are only taken when the match ends in a draw.")
        winner = match.home_team if home_score > away_score else match.away_team
        decided_by = Match.DECIDED_EXTRA_TIME if extra_time else Match.DECIDED_REGULAR
    else:
        if home_penalties is None or away_penalties is None:
            raise CompetitionError("The match is a draw — enter the penalty shoot-out result.")
        if home_penalties == away_penalties:
            raise CompetitionError("A penalty shoot-out cannot end level.")
        winner = match.home_team if home_penalties > away_penalties else match.away_team
        decided_by = Match.DECIDED_PENALTIES

    with transaction.atomic():
        match.home_score = home_score
        match.away_score = away_score
        match.home_penalties = home_penalties if decided_by == Match.DECIDED_PENALTIES else None
        match.away_penalties = away_penalties if decided_by == Match.DECIDED_PENALTIES else None
        match.decided_by = decided_by
        match.winner = winner
        match.is_finished = True
        match.save(update_fields=[
            'home_score', 'away_score', 'home_penalties', 'away_penalties',
            'decided_by', 'winner', 'is_finished',
        ])
        return refresh_knockout(tournament)


def finish_knockout_match(match, home_penalties=None, away_penalties=None, extra_time=False):
    """Finish a knockout match using the score from its recorded events."""
    home_score, away_score = match.score_from_events()
    return apply_knockout_result(match, home_score, away_score, home_penalties, away_penalties, extra_time)


def refresh_match_result(match):
    """
    Re-read the score of a finished match from its events.

    A knockout match whose corrected score is now a draw without a valid
    shoot-out is reopened (winner cleared) so the organiser can enter
    penalties. Returns conflicts from `refresh_knockout`.
    """
    home_score, away_score = match.score_from_events()
    match.home_score, match.away_score = home_score, away_score

    if not match.is_knockout:
        match.save(update_fields=['home_score', 'away_score'])
        return refresh_knockout(match.tournament)

    if home_score != away_score:
        match.winner = match.home_team if home_score > away_score else match.away_team
        match.home_penalties = match.away_penalties = None
        if match.decided_by == Match.DECIDED_PENALTIES:
            match.decided_by = Match.DECIDED_REGULAR
    elif (match.home_penalties is not None and match.away_penalties is not None
          and match.home_penalties != match.away_penalties):
        match.winner = match.home_team if match.home_penalties > match.away_penalties else match.away_team
        match.decided_by = Match.DECIDED_PENALTIES
    else:
        match.winner = None
        match.decided_by = ''
        match.is_finished = False

    match.save(update_fields=[
        'home_score', 'away_score', 'home_penalties', 'away_penalties',
        'decided_by', 'winner', 'is_finished',
    ])
    return refresh_knockout(match.tournament)


def after_group_match_finished(match):
    """Hook for finished group matches: fills the bracket once the group stage is done."""
    return refresh_knockout(match.tournament)


# ---------------------------------------------------------------------------
# Manual override
# ---------------------------------------------------------------------------

def set_slot_team(match, side, team):
    """
    Put `team` into a knockout slot by hand (e.g. after drawing lots), or
    pass `team=None` to return the slot to automatic filling.
    """
    if not match.is_knockout:
        raise CompetitionError("Only knockout matches have slots.")
    if match.has_started():
        raise CompetitionError("The match already started; teams can no longer be changed.")
    if team is not None and team.tournament_id != match.tournament_id:
        raise CompetitionError("Team belongs to another tournament.")

    slot = match.slots.get(side=side)
    other = match.away_team if side == MatchSlot.HOME else match.home_team
    if team is not None and other is not None and other.pk == team.pk:
        raise CompetitionError("A team cannot play against itself.")

    with transaction.atomic():
        attr = 'home_team' if side == MatchSlot.HOME else 'away_team'
        slot.is_manual_override = team is not None
        slot.save(update_fields=['is_manual_override'])
        if team is not None:
            setattr(match, attr, team)
            match.save(update_fields=[f'{attr}_id'])
        return refresh_knockout(match.tournament)


# ---------------------------------------------------------------------------
# Read models for views / API
# ---------------------------------------------------------------------------

def bracket_rounds(tournament):
    """[{'round', 'label', 'matches': [...]}] earliest round first; third place last."""
    matches = list(
        tournament.matches.filter(stage=Match.STAGE_KNOCKOUT)
        .select_related('home_team', 'away_team', 'winner', 'field')
        .prefetch_related('slots')
        .order_by('-round', 'is_third_place', 'bracket_position')
    )
    rounds = []
    for match in matches:
        key = 'third' if match.is_third_place else match.round
        if not rounds or rounds[-1]['key'] != key:
            rounds.append({
                'key': key,
                'round': match.round,
                'label': round_name(match.round, match.is_third_place),
                'matches': [],
            })
        rounds[-1]['matches'].append(match)
    return rounds
