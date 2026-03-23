from django.db import models
from django.core.exceptions import ValidationError
from django.conf import settings
from django.utils.text import slugify
from django.core.validators import MinValueValidator

class Tournament(models.Model):
    ROUND_ROBIN = 'round_robin'
    KNOCKOUT = 'knockout'

    FORMAT_CHOICES = [
        (ROUND_ROBIN, 'Round Robin'),
        # (KNOCKOUT, 'Knockout'),
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
    tournament_date = models.DateField(null=True, blank=True)

    points_for_win = models.PositiveSmallIntegerField(default=3)
    points_for_draw = models.PositiveSmallIntegerField(default=1)
    points_for_loss = models.PositiveSmallIntegerField(default=0)
    yellow_cards_for_suspension = models.PositiveSmallIntegerField(
        default=2,
        validators=[MinValueValidator(1)]
    )
    is_finished = models.BooleanField(default=False)

    format = models.CharField(
        max_length=20,
        choices=FORMAT_CHOICES,
        default=ROUND_ROBIN,
        help_text="Tournament format. Only 'round_robin' is implemented currently."
    )

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

    tournament_points = models.PositiveIntegerField(
        default=0,
        verbose_name="Tournament Points",
        )
        
    match_points = models.PositiveIntegerField(
        default=0,
        verbose_name="Match Points",
        )

    class Meta:
        unique_together = ('name', 'tournament')

    def __str__(self):
        return self.name

    def add_match_points(self, points):
        """Add points to the team's match points."""
        self.match_points += points
        self.save()
    
    def add_tournament_points(self, points):
        """Add points to the team's tournament points."""
        self.tournament_points += points
        self.save()
    
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

    def is_suspended(self):
        return self.is_muted or self.yellow_cards() >= self.team.tournament.yellow_cards_for_suspension or self.red_cards() >= 1
        
    def unmute(self):
        self.is_muted = False
        self.games_sat_out = 0
        self.match_events.filter(event_type__in=['yellow_card', 'red_card']).delete()
        self.save(update_fields=['is_muted', 'games_sat_out'])

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
    tournament = models.ForeignKey(
        Tournament,
        on_delete=models.CASCADE,
        related_name='matches'
    )

    home_team = models.ForeignKey(Team, on_delete=models.CASCADE, related_name='home_matches')
    away_team = models.ForeignKey(Team, on_delete=models.CASCADE, related_name='away_matches')

    home_score = models.PositiveIntegerField(default=0)
    away_score = models.PositiveIntegerField(default=0)

    is_finished = models.BooleanField(default=False)
    start_time = models.DateTimeField()
    field = models.ForeignKey(
        Field, 
        on_delete=models.PROTECT,
        null=False, 
        blank=False,
        )

    class Meta:
        unique_together = ('home_team', 'away_team', 'start_time')
        ordering = ['start_time']
        verbose_name = "Match"
        verbose_name_plural = "Matches"

    def __str__(self):
        return f"{self.home_team.name} vs {self.away_team.name}"
    
    def clean(self):
        super().clean()
        if self.home_team == self.away_team:
            raise ValidationError("A team cannot play against itself.")

        if self.home_team.tournament != self.tournament or self.away_team.tournament != self.tournament:
            raise ValidationError("Both teams must belong to the same tournament as the match.")

        overlapping = Match.objects.filter(
            field=self.field,
            start_time=self.start_time
        ).exclude(pk=self.pk)

        if overlapping.exists():
            raise ValidationError("Another match is already scheduled at this field and time.")

    def apply_result(self):
        if self.is_finished:
            return

        tournament = self.tournament

        # Calculate goals for each team
        home_goals = self.events.filter(event_type='goal', team=self.home_team).count()
        home_goals += self.events.filter(event_type='own_goal', team=self.away_team).count()

        away_goals = self.events.filter(event_type='goal', team=self.away_team).count()
        away_goals += self.events.filter(event_type='own_goal', team=self.home_team).count()

        # Set the score fields
        self.home_score = home_goals
        self.away_score = away_goals

        # Assign points
        if home_goals > away_goals:
            self.home_team.tournament_points += tournament.points_for_win
            self.away_team.tournament_points += tournament.points_for_loss
        elif away_goals > home_goals:
            self.away_team.tournament_points += tournament.points_for_win
            self.home_team.tournament_points += tournament.points_for_loss
        else:
            self.home_team.tournament_points += tournament.points_for_draw
            self.away_team.tournament_points += tournament.points_for_draw

        # Save everything
        self.home_team.save()
        self.away_team.save()
        self.is_finished = True
        self.save()

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