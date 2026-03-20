import re
from django import forms
from django.utils.text import slugify
from datetime import datetime, time, date
from .models import Team, Match, Player, GoalEvent, Field, MatchEvent, Tournament
from .utils import recalculate_match_points

class TournamentCreateForm(forms.ModelForm):
    class Meta:
        model = Tournament
        fields = ['name', 'points_for_win', 'points_for_draw']
        labels = {
            'points_for_win': 'Points for win',
            'points_for_draw': 'Points for draw',
        }

    def clean(self):
        cleaned_data = super().clean()
        win = cleaned_data.get('points_for_win')
        draw = cleaned_data.get('points_for_draw')
        if win is not None and draw is not None and win <= draw:
            raise forms.ValidationError(
                "Points for win must be greater than points for draw."
            )
        return cleaned_data

class TournamentUpdateForm(forms.ModelForm):
    class Meta:
        model = Tournament
        fields = ['name', 'tournament_date', 'points_for_win', 'points_for_draw']
        labels = {
            'points_for_win': 'Points for win',
            'points_for_draw': 'Points for draw',
        }
        widgets = {
            'tournament_date': forms.DateInput(attrs={'type': 'date'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # lock points fields if scored matches exist
        if self.instance and self.instance.pk:
            if self.instance.matches.filter(is_finished=True).exists():
                self.fields['points_for_win'].disabled = True
                self.fields['points_for_draw'].disabled = True
                self.fields['points_for_win'].help_text = (
                    "Cannot be changed after matches have been scored."
                )
                self.fields['points_for_draw'].help_text = (
                    "Cannot be changed after matches have been scored."
                )

    def clean(self):
        cleaned_data = super().clean()
        win = cleaned_data.get('points_for_win')
        draw = cleaned_data.get('points_for_draw')
        if win is not None and draw is not None and win <= draw:
            raise forms.ValidationError(
                "Points for win must be greater than points for draw."
            )
        return cleaned_data

    def clean_name(self):
        name = self.cleaned_data['name'].strip()
        if not name:
            raise forms.ValidationError("Tournament name cannot be empty.")
        return name
        
class TeamCreateForm(forms.ModelForm):
    class Meta:
        model = Team
        fields = ['name',]
        widgets =  {
            'name': forms.Textarea(
                attrs = {
                    'rows': 4,
                    'placeholder': 'Enter one name of team per line.',
                    'class': 'form-input',
                }
            )
        }
        
    def clean_name(self):
        name = self.cleaned_data['name'].strip()

        names = [n.strip().title() for n in name.splitlines() if n.strip()]
        for n in names:
            if not re.match(r'^[\w\s\-&]{1,50}$', n):
                raise forms.ValidationError("Invalid team name. Use letters, numbers, dashes or '&'.")

        return self.cleaned_data['name'].strip()

class MatchCreateForm(forms.ModelForm):
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
        tournament = kwargs.pop('tournament', None)
        super().__init__(*args, **kwargs)

        if tournament:
            self.fields['home_team'].queryset = Team.objects.filter(tournament=tournament)
            self.fields['away_team'].queryset = Team.objects.filter(tournament=tournament)
            self.fields['field'].queryset = Field.objects.filter(tournament=tournament)

        # If initial data exists, convert to proper format for datetime-local input
        if self.instance and self.instance.start_time:
            self.initial['start_time'] = self.instance.start_time.strftime('%Y-%m-%dT%H:%M')
        
        self.fields['field'].empty_label = None

class FieldCreateForm(forms.ModelForm):
    class Meta:
        model = Field
        fields = ['name']

    def __init__(self, *args, **kwargs):
        self.tournament = kwargs.pop('tournament', None)
        super().__init__(*args, **kwargs)

    def clean_name(self):
        name = self.cleaned_data['name'].strip().title()
        if self.tournament and Field.objects.filter(name=name, tournament=self.tournament).exists():
            raise forms.ValidationError(f'A field named "{name}" already exists.')
        return name

class MatchEditForm(forms.ModelForm):
    class Meta:
        model = Match
        fields = ['home_score', 'away_score']
        labels = {
            'home_score': 'Home Team Score',
            'away_score': 'Away Team Score',
        }

    def __init__(self, *args, **kwargs):
        self.match = kwargs.get('instance')
        super().__init__(*args, **kwargs)

        if self.match:
            self.fields['home_score'].label = self.match.home_team.name
            self.fields['away_score'].label = self.match.away_team.name

    def save(self, commit=True):
        match = super().save(commit=False)

        if match.is_finished:
            self._reverse_previous_points()

        self._apply_match_points(match)

        match.is_finished = True
        if commit:
            match.save()

        recalculate_match_points(
            match=self.match,
            new_home_score=match.home_score,
            new_away_score=match.away_score,
        )

        match.is_finished = True
        
        if commit:
            match.save()

        return match

class MatchRescheduleForm(forms.Form):
    start_time = forms.TimeField(
        widget=forms.TimeInput(attrs={'type': 'time'}),
        label="Start Time"
    )
    field = forms.ModelChoiceField(
        queryset=Field.objects.none(),
        label="Field",
        empty_label=None
    )
    propagate = forms.BooleanField(
        required=False,
        label="Shift all subsequent matches by the same delay"
    )

    def __init__(self, *args, **kwargs):
        tournament = kwargs.pop('tournament')
        super().__init__(*args, **kwargs)
        self.fields['field'].queryset = Field.objects.filter(tournament=tournament)
        
class MatchEventForm(forms.ModelForm):
    player = forms.CharField()
    team = forms.CharField()

    class Meta:
        model = MatchEvent
        fields = ['event_type',]

    def __init__(self, *args, **kwargs):
        self.match = kwargs.pop('match', None)
        super().__init__(*args, **kwargs)
        
    def clean(self):
        cleaned_data = super().clean()

        player_name = cleaned_data.get('player')
        team_key = cleaned_data.get('team')

        if not player_name:
            raise forms.ValidationError("Player name is required.")
        
        if not self.match:
            raise forms.ValidationError("Match instance is required.")
        
        if team_key == 'home':
            team_instance = self.match.home_team
        elif team_key == 'away':
            team_instance = self.match.away_team
        else:
            raise forms.ValidationError("Invalid team selection.")
            
        player, _ = Player.objects.get_or_create(name=player_name.strip(), team=team_instance)

        cleaned_data['player_name'] = player_name.strip()
        cleaned_data['team_instance'] = team_instance

        return cleaned_data

    def save(self, commit=True):
        event = super().save(commit=False)

        team = self.cleaned_data['team_instance']
        player_name = self.cleaned_data['player_name']

        player, _ = Player.objects.get_or_create(
            name = player_name,
            team = team
        )

        event.match = self.match
        event.player = self.cleaned_data['player']
        event.team = self.cleaned_data['team']

        if commit:
            event.full_clean()
            event.save()

        return event

class TournamentScheduleForm(forms.Form):
    start_date = forms.DateField(
        label="Tournament Date",
        initial=date.today,
        widget=forms.DateInput(attrs={'type': 'date'})
    )
    start_time = forms.TimeField(
        label="First Match Start Time",
        initial=time(10, 0),
        widget=forms.TimeInput(attrs={'type': 'time'})
    )
    has_halves = forms.BooleanField(
        label="Split into two halves",
        required=False,
        initial=False
    )
    half_duration = forms.IntegerField(
        label="Half Duration (minutes)",
        initial=15,
        min_value=1,
        required=False
    )
    half_time_break = forms.IntegerField(
        label="Half-Time Break (minutes)",
        initial=5,
        min_value=0,
        required=False
    )
    game_duration = forms.IntegerField(
        label="Game Duration (minutes)",
        initial=15,
        min_value=1,
        required=False
    )
    pause_duration = forms.IntegerField(
        label="Pause Between Matches (minutes)",
        initial=5,
        min_value=0
    )

    def clean(self):
        cleaned_data = super().clean()
        has_halves = cleaned_data.get('has_halves')

        if has_halves:
            if not cleaned_data.get('half_duration'):
                raise forms.ValidationError("Half duration is required when using halves.")
            if cleaned_data.get('half_time_break') is None:
                raise forms.ValidationError("Half-time break is required when using halves.")
        else:
            if not cleaned_data.get('game_duration'):
                raise forms.ValidationError("Game duration is required.")

        return cleaned_data