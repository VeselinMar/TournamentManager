from django.db import models
from django.core.exceptions import ValidationError
from django.conf import settings


class Tournament(models.Model):
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
    is_finished = models.BooleanField(
        default=False,
    )

    def __str__(self):
        return f"{self.name} ({self.owner.email})"

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
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

    goals = models.PositiveIntegerField(
        default=0,
        verbose_name="Goals Scored",
        help_text="Total goals scored by the player."
        )

    own_goals = models.PositiveIntegerField(
        default=0,
        verbose_name="Own Goals",
        help_text="Total own goals scored by the player.")
    
    yellow_cards = models.PositiveIntegerField(
        default=0,
        verbose_name="Yellow Cards",
        help_text="Total yellow cards received by the player."
        )

    red_cards = models.PositiveIntegerField(
        default=0
        )
        
    is_allowed_to_play = models.BooleanField(
        default=True,
        verbose_name="Allowed to Play",
        help_text="Indicates if the player is allowed to play in the next match.")

    class Meta:
        unique_together = ('name', 'team')
        verbose_name = "Player"
        verbose_name_plural = "Players"

    def __str__(self):
        return f"Player: {self.name} (Team: {self.team.name})"

    def update_eligibility(self):
        """Player who has a red card is forced to sit out the next match."""
        self.is_allowed_to_play = not (self.red_cards >= 1 or self.yellow_cards >= 2)
    
    def save(self, *args, **kwargs):
        self.update_eligibility()
        super().save(*args, **kwargs)

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

    def apply_result(self):
        if self.is_finished:
            return

        # Calculate goals for each team
        home_goals = self.events.filter(event_type='goal', team=self.home_team).count()
        home_goals += self.events.filter(event_type='own_goal', team=self.away_team).count()

        away_goals = self.events.filter(event_type='goal', team=self.away_team).count()
        away_goals += self.events.filter(event_type='own_goal', team=self.home_team).count()

        # Set the score fields
        self.home_score = home_goals
        self.away_score = away_goals

        for event in self.events.all():
            event.apply_event_effects()

        # Assign points
        if home_goals > away_goals:
            self.home_team.tournament_points += 3
        elif away_goals > home_goals:
            self.away_team.tournament_points += 3
        else:
            self.home_team.tournament_points += 1
            self.away_team.tournament_points += 1

        # Save everything
        self.home_team.save()
        self.away_team.save()
        self.is_finished = True
        self.save()
    
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

    def apply_event_effects(self):
        if not self.player:
            return

        if self.event_type == 'goal':
            self.player.goals += 1
        elif self.event_type == 'own_goal':
            self.player.own_goals += 1
        elif self.event_type == 'yellow_card':
            self.player.yellow_cards += 1
        elif self.event_type == 'red_card':
            self.player.red_cards += 1

        self.player.update_eligibility()
        self.player.save()
    
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
    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)

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
        if self.player and not self.player.is_allowed_to_play:
            raise ValidationError("Suspended player cannot score.")
        super().save(*args, **kwargs)

    def __str__(self):
        return f"GOAL: {self.player} for {self.team} in {self.match}"
    
    def clean(self):
        super().clean()
        if self.event_type != 'goal':
            raise ValidationError("This event must be a goal.")
