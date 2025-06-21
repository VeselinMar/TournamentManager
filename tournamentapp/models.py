from django.db import models

class Team(models.Model):
    name = models.CharField(max_length=100, unique=True)
    logo = models.ImageField(upload_to='team_logos/', blank=True, null=True)
    points = models.PositiveIntegerField(default=0)

    def __str__(self):
        return self.name

class Player(models.Model):
    name = models.CharField(max_length=100)  # Optional if created automatically
    team = models.ForeignKey(Team, on_delete=models.CASCADE, related_name='players')
    goals = models.PositiveIntegerField(default=0)
    yellow_cards = models.PositiveIntegerField(default=0)
    red_cards = models.PositiveIntegerField(default=0)
    is_allowed_to_play = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.name or 'Unnamed Player'} ({self.team.name})"

    def save(self, *args, **kwargs):
        self.update_eligibility()
        super().save(*args, **kwargs)

    def update_eligibility(self):
        """Disqualify if player has 1 red card or 2+ yellow cards"""
        self.is_allowed_to_play = not (self.red_cards >= 1 or self.yellow_cards >= 2)

class Match(models.Model):
    FIELD_CHOICES = (
        ('A', 'Field A'),
        ('B', 'Field B'),
    )

    home_team = models.ForeignKey(Team, on_delete=models.CASCADE, related_name='home_matches')
    away_team = models.ForeignKey(Team, on_delete=models.CASCADE, related_name='away_matches')

    home_score = models.PositiveIntegerField(default=0)
    away_score = models.PositiveIntegerField(default=0)

    is_finished = models.BooleanField(default=False)

    start_time = models.TimeField()
    field = models.CharField(max_length=1, choices=FIELD_CHOICES)

    def __str__(self):
        return f"{self.home_team.name} vs {self.away_team.name}"

    def apply_result(self):
        if self.is_finished:
            return

        if self.home_score > self.away_score:
            self.home_team.points += 3
        elif self.home_score < self.away_score:
            self.away_team.points += 3
        else:
            self.home_team.points += 1
            self.away_team.points += 1

        self.home_team.save()
        self.away_team.save()
        self.is_finished = True
        self.save()

class Goal(models.Model):
    match = models.ForeignKey(Match, on_delete=models.CASCADE, related_name='goals')
    team = models.ForeignKey(Team, on_delete=models.CASCADE)
    player = models.ForeignKey(Player, on_delete=models.CASCADE)
    minute = models.PositiveIntegerField(null=True, blank=True)


    def __str__(self):
        return f"{self.player.name} scored for {self.team.name} in match: {self.match.home_team.name} - {self.match.away_team.name}"


    def save(self, *args, **kwargs):
        created = self.pk is None
        super().save(*args, **kwargs)
        if created:
            self.player.goals += 1
            self.player.save()
