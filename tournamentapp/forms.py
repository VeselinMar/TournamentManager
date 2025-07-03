from django import forms
from .models import Team, Match, Player, GoalEvent

class TeamForm(forms.ModelForm):
    class Meta:
        model = Team
        fields = ['name', 'logo']

class MatchForm(forms.ModelForm):
    class Meta:
        model = Match
        fields = ['home_team', 'away_team', 'start_time', 'field']

    def clean(self):
        cleaned_data = super().clean()
        home_team = cleaned_data.get('home_team')
        away_team = cleaned_data.get('away_team')

        if home_team == away_team:
            raise forms.ValidationError("Home and Away teams must be different.")


class MatchEditForm(forms.ModelForm):
    home_scorers = forms.CharField(
        widget=forms.Textarea(attrs={'placeholder': 'One scorer per line for Home Team'}),
        required=False,
        label="Home Scorers"
    )
    away_scorers = forms.CharField(
        widget=forms.Textarea(attrs={'placeholder': 'One scorer per line for Away Team'}),
        required=False,
        label="Away Scorers"
    )

    class Meta:
        model = Match
        fields = ['home_score', 'away_score']

    def __init__(self, *args, **kwargs):
        self.match = kwargs.get('instance')
        super().__init__(*args, **kwargs)

        if self.match:
            self.fields['home_score'].label = self.match.home_team.name
            self.fields['away_score'].label = self.match.away_team.name

    def save(self, commit=True):
        match = super().save(commit=False)

        # Step 1: Reverse previous match effects
        if match.is_finished:
            self._reverse_previous_results()

        # Step 2: Apply new match points
        self._apply_match_points(match)

        match.is_finished = True
        match.save()

        # Step 3: Register new goal events
        self._register_goal_events(match)

        return match

    def _reverse_previous_results(self):
        match = self.match

        # Reverse tournament points
        if match.home_score > match.away_score:
            match.home_team.tournament_points = max(0, match.home_team.tournament_points - 3)
        elif match.home_score < match.away_score:
            match.away_team.tournament_points = max(0, match.away_team.tournament_points - 3)
        else:
            match.home_team.tournament_points = max(0, match.home_team.tournament_points - 1)
            match.away_team.tournament_points = max(0, match.away_team.tournament_points - 1)

        match.home_team.save()
        match.away_team.save()

        # Reverse player goal counters and delete goal events
        for goal_event in GoalEvent.objects.filter(match=match):
            player = goal_event.player
            if player and player.goals > 0:
                player.goals -= 1
                player.save()
            goal_event.delete()

    def _apply_match_points(self, match):
        if match.home_score > match.away_score:
            match.home_team.tournament_points += 3
        elif match.home_score < match.away_score:
            match.away_team.tournament_points += 3
        else:
            match.home_team.tournament_points += 1
            match.away_team.tournament_points += 1

        match.home_team.save()
        match.away_team.save()

    def _register_goal_events(self, match):
        home_scorers = self.cleaned_data.get('home_scorers', '').splitlines()
        away_scorers = self.cleaned_data.get('away_scorers', '').splitlines()

        for name in map(str.strip, home_scorers):
            if name:
                player, _ = Player.objects.get_or_create(name=name, team=match.home_team)
                GoalEvent.objects.create(match=match, team=match.home_team, player=player, minute=0)
                player.goals += 1
                player.save()

        for name in map(str.strip, away_scorers):
            if name:
                player, _ = Player.objects.get_or_create(name=name, team=match.away_team)
                GoalEvent.objects.create(match=match, team=match.away_team, player=player, minute=0)
                player.goals += 1
                player.save()
