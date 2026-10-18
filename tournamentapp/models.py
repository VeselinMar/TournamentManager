from django.db import models
from django.core.exceptions import ValidationError
from django.conf import settings
from django.utils.text import slugify
from django.core.validators import MinValueValidator

class Tournament(models.Model):
    ROUND_ROBIN = 'round_robin'
    GROUPS_KNOCKOUT = 'groups_knockout'

    FORMAT_CHOICES = [
        (ROUND_ROBIN, 'Round Robin'),
        (GROUPS_KNOCKOUT, 'Groups + Knockout'),
    ]

    DRAW_PENALTIES = 'penalties'
    DRAW_EXTRA_TIME = 'extra_time'
    KNOCKOUT_DRAW_CHOICES = [
        (DRAW_PENALTIES, 'Straight to penalties'),
        (DRAW_EXTRA_TIME, 'Extra time, then penalties'),
    ]

    name = models.CharField(max_length=100)
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='tournaments'
    )
    slug = models.SlugField(
        max_length=255,
        unique=True,
        blank=True
    )
    cache_version = models.PositiveIntegerField(default=1)
    tournament_date = models.DateField(null=True, blank=True)
    show_leaderboard = models.BooleanField(default=True)
    show_vendors = models.BooleanField(default=True)
    show_side_events = models.BooleanField(default=True)
    show_announcements = models.BooleanField(default=True)

    points_for_win = models.PositiveSmallIntegerField(default=3)
    points_for_draw = models.PositiveSmallIntegerField(default=1)
    points_for_loss = models.PositiveSmallIntegerField(default=0)
    yellow_cards_for_suspension = models.PositiveSmallIntegerField(
        default=2,
        validators=[MinValueValidator(1)]
    )
    is_finished = models.BooleanField(default=False)

    TIEBREAK_HEAD_TO_HEAD = 'head_to_head'
    TIEBREAK_GOAL_DIFFERENCE = 'goal_difference'
    TIEBREAK_CHOICES = [
        (TIEBREAK_HEAD_TO_HEAD, 'Head-to-head first, then overall goal difference (UEFA style)'),
        (TIEBREAK_GOAL_DIFFERENCE, 'Overall goal difference first, then head-to-head (FIFA style)'),
    ]
    tiebreak_rule = models.CharField(
        max_length=20,
        choices=TIEBREAK_CHOICES,
        default=TIEBREAK_HEAD_TO_HEAD,
        help_text="How teams level on points are ranked.",
    )

    format = models.CharField(
        max_length=20,
        choices=FORMAT_CHOICES,
        default=ROUND_ROBIN,
        help_text="Round robin: everyone plays everyone. Groups + Knockout: group stage followed by a bracket."
    )

    # --- Groups + Knockout settings (ignored for round robin)
    qualifiers_per_group = models.PositiveSmallIntegerField(
        default=2,
        validators=[MinValueValidator(1)],
        help_text="Teams that qualify directly from each group.",
    )
    best_placed_qualifiers = models.PositiveSmallIntegerField(
        default=0,
        help_text="Additional qualifiers: the best teams in the next group position "
                  "(e.g. best third-placed teams).",
    )
    third_place_match = models.BooleanField(default=False)
    knockout_draw_resolution = models.CharField(
        max_length=20,
        choices=KNOCKOUT_DRAW_CHOICES,
        default=DRAW_PENALTIES,
        help_text="What happens when a knockout match ends in a draw.",
    )
    extra_time_duration = models.PositiveSmallIntegerField(
        default=10,
        validators=[MinValueValidator(1)],
        help_text="Total extra time in minutes (only used with 'Extra time, then penalties').",
    )

    @property
    def uses_groups(self):
        return self.format == self.GROUPS_KNOCKOUT

    @property
    def allows_extra_time(self):
        return self.knockout_draw_resolution == self.DRAW_EXTRA_TIME

    def __str__(self):
        return f"{self.name} ({self.owner.email})"

    def save(self, *args, **kwargs):
        if not self.pk or Tournament.objects.filter(pk=self.pk).exclude(name=self.name).exists():
            base = slugify(self.name)
            slug = base
            n = 1
            while Tournament.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f"{base}-{n}"
                n += 1
            self.slug = slug
        super().save(*args, **kwargs)
    
class Group(models.Model):
    tournament = models.ForeignKey(
        Tournament,
        on_delete=models.CASCADE,
        related_name='groups',
    )
    name = models.CharField(max_length=20)
    order = models.PositiveSmallIntegerField(default=0)

    class Meta:
        unique_together = ('tournament', 'name')
        ordering = ['order', 'name']

    def __str__(self):
        return f"Group {self.name}"


class Team(models.Model):
    name = models.CharField(
        max_length=100,
        verbose_name="Team Name",
        )

    tournament = models.ForeignKey(
        Tournament,
        on_delete=models.CASCADE,
        related_name='teams'
    )

    logo = models.ImageField(
        upload_to='team_logos/',
        blank=True,
        null=True,
        verbose_name="Team Logo",
        )

    group = models.ForeignKey(
        Group,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='teams',
    )

    # Points are not stored: standings are calculated from finished
    # group-stage matches (see utils.get_team_standings).

    class Meta:
        unique_together = ('name', 'tournament')

    def __str__(self):
        return self.name
    
class Player(models.Model):
    name = models.CharField(
        max_length=100,
        help_text="Enter the player's name or jersey number.",
        verbose_name="Player Name",
        blank=False,
        null=False,
        )
    team = models.ForeignKey(
        Team,
        on_delete=models.CASCADE,
        related_name='players',
        verbose_name="Team",
        help_text="Select the team this player belongs to.",
        blank=False,
        null=False,
        )

    is_muted = models.BooleanField(
        default=False,
        )
    games_sat_out = models.PositiveSmallIntegerField(
        default=0,
        )
    suspension_cleared_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Cards given before this moment no longer count towards a suspension.",
        )


    class Meta:
        unique_together = ('name', 'team')
        verbose_name = "Player"
        verbose_name_plural = "Players"

    def __str__(self):
        return f"Player: {self.name} (Team: {self.team.name})"

    def goals(self):
        return self.match_events.filter(event_type='goal').count()

    def own_goals(self):
        return self.match_events.filter(event_type='own_goal').count()

    def yellow_cards(self):
        return self.match_events.filter(event_type='yellow_card').count()

    def red_cards(self):
        return self.match_events.filter(event_type='red_card').count()

    def _active_card_events(self):
        events = self.match_events.all()
        if self.suspension_cleared_at:
            events = events.filter(created_at__gt=self.suspension_cleared_at)
        return events

    def active_yellow_cards(self):
        """Yellow cards that still count towards a suspension."""
        return self._active_card_events().filter(event_type='yellow_card').count()

    def active_red_cards(self):
        """Red cards that still count towards a suspension."""
        return self._active_card_events().filter(event_type='red_card').count()

    def is_suspended(self):
        return (
            self.is_muted
            or self.active_yellow_cards() >= self.team.tournament.yellow_cards_for_suspension
            or self.active_red_cards() >= 1
        )

    def unmute(self):
        """Lift the suspension. Card history is kept for stats; only the
        suspension counter is reset."""
        from django.utils import timezone
        self.is_muted = False
        self.games_sat_out = 0
        self.suspension_cleared_at = timezone.now()
        self.save(update_fields=['is_muted', 'games_sat_out', 'suspension_cleared_at'])

class Field(models.Model):
    name = models.CharField(
        max_length=50,
        default='Main Field'
        )
    tournament = models.ForeignKey(
        Tournament,
        on_delete=models.CASCADE,
        related_name='fields'
    )
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='fields'
    )

    class Meta:
        unique_together = ('name', 'tournament')
        verbose_name = "Field"
        verbose_name_plural = "Fields"

    def __str__(self):
        return f"{self.name}"

    @property
    def has_matches(self):
        return self.match_set.exists()

class Match(models.Model):
    STAGE_GROUP = 'group'
    STAGE_KNOCKOUT = 'knockout'
    STAGE_CHOICES = [
        (STAGE_GROUP, 'Group stage'),
        (STAGE_KNOCKOUT, 'Knockout'),
    ]

    DECIDED_REGULAR = 'regular'
    DECIDED_EXTRA_TIME = 'extra_time'
    DECIDED_PENALTIES = 'penalties'
    DECIDED_CHOICES = [
        (DECIDED_REGULAR, 'Regular time'),
        (DECIDED_EXTRA_TIME, 'Extra time'),
        (DECIDED_PENALTIES, 'Penalties'),
    ]

    tournament = models.ForeignKey(
        Tournament,
        on_delete=models.CASCADE,
        related_name='matches'
    )

    stage = models.CharField(max_length=10, choices=STAGE_CHOICES, default=STAGE_GROUP)
    group = models.ForeignKey(
        Group,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='matches',
    )
    # Group stage: matchday number. Knockout: number of teams in the round
    # (8 = quarter-final, 4 = semi-final, 2 = final).
    round = models.PositiveSmallIntegerField(null=True, blank=True)
    bracket_position = models.PositiveSmallIntegerField(null=True, blank=True)
    is_third_place = models.BooleanField(default=False)

    # Knockout matches start without teams; they are filled in as results come in.
    home_team = models.ForeignKey(Team, on_delete=models.CASCADE, related_name='home_matches', null=True, blank=True)
    away_team = models.ForeignKey(Team, on_delete=models.CASCADE, related_name='away_matches', null=True, blank=True)

    home_score = models.PositiveIntegerField(default=0)
    away_score = models.PositiveIntegerField(default=0)

    home_penalties = models.PositiveSmallIntegerField(null=True, blank=True)
    away_penalties = models.PositiveSmallIntegerField(null=True, blank=True)
    decided_by = models.CharField(max_length=12, choices=DECIDED_CHOICES, blank=True, default='')
    winner = models.ForeignKey(
        Team,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='knockout_wins',
    )

    is_finished = models.BooleanField(default=False)
    start_time = models.DateTimeField()
    field = models.ForeignKey(
        Field, 
        on_delete=models.CASCADE,
        null=False, 
        blank=False,
        )

    class Meta:
        unique_together = ('home_team', 'away_team', 'start_time')
        ordering = ['start_time']
        verbose_name = "Match"
        verbose_name_plural = "Matches"

    def __str__(self):
        return f"{self.home_label} vs {self.away_label}"

    # ---- labels -----------------------------------------------------------

    def _side_label(self, side):
        team = self.home_team if side == 'home' else self.away_team
        if team is not None:
            return team.name
        if self.pk is None:
            return 'TBD'
        slot = next((s for s in self.slots.all() if s.side == side), None)
        return slot.placeholder if slot else 'TBD'

    @property
    def home_label(self):
        return self._side_label('home')

    @property
    def away_label(self):
        return self._side_label('away')

    @property
    def is_knockout(self):
        return self.stage == self.STAGE_KNOCKOUT

    @property
    def teams_known(self):
        return self.home_team_id is not None and self.away_team_id is not None

    @property
    def round_label(self):
        """'Group A', 'Semi-final 1', 'Final', 'Third place' or ''."""
        if self.is_knockout:
            from .competition import round_name
            name = round_name(self.round, self.is_third_place)
            if self.is_third_place or self.round == 2:
                return name
            return f"{name} {self.bracket_position}"
        if self.group_id:
            return str(self.group)
        return ''

    def has_started(self):
        return self.is_finished or self.events.exists()

    def clean(self):
        super().clean()
        if self.home_team_id and self.home_team_id == self.away_team_id:
            raise ValidationError("A team cannot play against itself.")

        for team in (self.home_team, self.away_team):
            if team is not None and team.tournament_id != self.tournament_id:
                raise ValidationError("Both teams must belong to the same tournament as the match.")

        overlapping = Match.objects.filter(
            field=self.field,
            start_time=self.start_time
        ).exclude(pk=self.pk)

        if overlapping.exists():
            raise ValidationError("Another match is already scheduled at this field and time.")

    def score_from_events(self):
        """Return (home_goals, away_goals) computed from recorded events.
        Own goals count for the opposing team."""
        home_goals = self.events.filter(event_type='goal', team=self.home_team).count()
        home_goals += self.events.filter(event_type='own_goal', team=self.away_team).count()

        away_goals = self.events.filter(event_type='goal', team=self.away_team).count()
        away_goals += self.events.filter(event_type='own_goal', team=self.home_team).count()
        return home_goals, away_goals

    def apply_result(self):
        """Finish a group-stage match using the score from its events.
        Points are derived from finished matches, so nothing else is stored."""
        if self.is_finished:
            return

        self.home_score, self.away_score = self.score_from_events()
        self.is_finished = True
        self.save(update_fields=['home_score', 'away_score', 'is_finished'])


class MatchSlot(models.Model):
    """Where a knockout participant comes from."""
    HOME = 'home'
    AWAY = 'away'
    SIDE_CHOICES = [(HOME, 'Home'), (AWAY, 'Away')]

    SOURCE_SEED = 'seed'
    SOURCE_WINNER = 'match_winner'
    SOURCE_LOSER = 'match_loser'
    SOURCE_CHOICES = [
        (SOURCE_SEED, 'Seed from group stage'),
        (SOURCE_WINNER, 'Winner of match'),
        (SOURCE_LOSER, 'Loser of match'),
    ]

    match = models.ForeignKey(Match, on_delete=models.CASCADE, related_name='slots')
    side = models.CharField(max_length=4, choices=SIDE_CHOICES)
    source_type = models.CharField(max_length=12, choices=SOURCE_CHOICES)
    seed = models.PositiveSmallIntegerField(null=True, blank=True)
    source_match = models.ForeignKey(
        Match,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='feeds',
    )
    placeholder = models.CharField(max_length=60, help_text="Shown until the team is known.")
    is_manual_override = models.BooleanField(default=False)

    class Meta:
        unique_together = ('match', 'side')

    def __str__(self):
        return f"{self.match_id}/{self.side}: {self.placeholder}"

class MatchEvent(models.Model):
    EVENT_TYPES = (
        ('goal', 'Goal'),
        ('yellow_card', 'Yellow Card'),
        ('red_card', 'Red Card'),
        ('substitution', 'Substitution'),
        ('own_goal', 'Own Goal'),
    )

    match = models.ForeignKey(
        Match,
        on_delete=models.CASCADE,
        related_name='events'
    )
    event_type = models.CharField(
        max_length=20,
        choices=EVENT_TYPES,
        help_text="Type of event that occurred during the match.",
        verbose_name="Event Type",
    )
    minute = models.PositiveIntegerField(
        help_text="Minute in which the event occurred.",
        verbose_name="Minute",
        null=True,
        blank=True,
    )
    team = models.ForeignKey(
        Team,
        on_delete=models.CASCADE,
        related_name='match_events',
        help_text="Team involved in the event.",
        verbose_name="Team",
    )
    player = models.ForeignKey(
        Player,
        on_delete=models.SET_NULL,
        related_name='match_events',
        help_text="Player involved in the event.",
        verbose_name="Player",
        null=True,
        blank=True,
    )
    substitute_player = models.ForeignKey(
        Player,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='substitute_entries',
        help_text="Only for substitutions"
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text="Timestamp when the event was created.",
        verbose_name="Created At",
    )

    class Meta:
        ordering = ['minute', 'created_at']
        verbose_name = "Match Event"
        verbose_name_plural = "Match Events"

    def __str__(self):
        minute = f"{self.minute}'" if self.minute else "?"
        if self.event_type == 'substitution':
            return f"Substitution - {self.player} → {self.substitute_player} ({self.team}) at {minute}"
        elif self.event_type == 'own_goal':
            return f"Own Goal - {self.player} ({self.team}) at {minute}"
        else:
            return f"{self.get_event_type_display()} - {self.player} ({self.team}) at {minute}"

    def clean(self):
        if self.substitute_player and self.substitute_player.team != self.team:
            raise ValidationError("Substitute must be from the same team.")
        if self.event_type == 'substitution' and not self.substitute_player:
            raise ValidationError("Substitution must specify a substitute player.")

class GoalManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(event_type='goal')

class GoalEvent(MatchEvent):
    objects = GoalManager()

    class Meta:
        proxy = True

    def save(self, *args, **kwargs):
        self.event_type = 'goal'
        self.clean()
        if self.player and self.player.is_suspended():
            raise ValidationError("Suspended player cannot score.")
        super().save(*args, **kwargs)

    def __str__(self):
        return f"GOAL: {self.player} for {self.team} in {self.match}"

    def clean(self):
        super().clean()
        if self.event_type != 'goal':
            raise ValidationError("This event must be a goal.")