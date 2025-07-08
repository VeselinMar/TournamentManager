import re
from django import forms
from .models import Team, Match, Player, GoalEvent, Field

class TeamForm(forms.ModelForm):
    class Meta:
        model = Team
        fields = ['name', 'logo']
        
    def clean_name(self):
        name = self.cleaned_data['name'].strip().title()

        # Basic validation: letters, numbers, spaces, dashes, ampersand
        if not re.match(r'^[\w\s\-&]{1,50}$', name):
            raise forms.ValidationError("Invalid team name. Use letters, numbers, dashes or '&'.")

        return name

class MatchForm(forms.ModelForm):
    class Meta:
        model = Match
        fields = ['home_team', 'away_team', 'start_time', 'field']
        widgets = {
            'start_time': forms.DateTimeInput(attrs={
                'type': 'datetime-local',
                }
                ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # If initial data exists, convert to proper format for datetime-local input
        if self.instance and self.instance.start_time:
            self.initial['start_time'] = self.instance.start_time.strftime('%Y-%m-%dT%H:%M')
        
        if not self.initial.get('field'):
            try:
                default_field = Field.objects.get(name='Main Field')
                self.fields['field'].initial = default_field.id
            except Field.DoesNotExist:
                pass
        
        self.fields['field'].empty_label = None

    def clean_start_time(self):
        start_time = self.cleaned_data['start_time']
        return start_time


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
