import re
from django import forms
from .models import Team, Match, Player, GoalEvent, Field, MatchEvent

class TeamCreateForm(forms.ModelForm):
    class Meta:
        model = Team
        fields = ['name',]
        
    def clean_name(self):
        name = self.cleaned_data['name'].strip().title()

        # Basic validation: letters, numbers, spaces, dashes, ampersand
        if not re.match(r'^[\w\s\-&]{1,50}$', name):
            raise forms.ValidationError("Invalid team name. Use letters, numbers, dashes or '&'.")

        return name

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

class FieldCreateForm(forms.ModelForm):
    class Meta:
        model = Field
        fields = ['name',]
    
    def clean_name(self):
        name = self.cleaned_data['name'].strip().title()
    
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

        return match

    def _reverse_previous_points(self):
        match = self.match

        if match.home_score > match.away_score:
            match.home_team.tournament_points = max(0, match.home_team.tournament_points - 3)
        elif match.home_score < match.away_score:
            match.away_team.tournament_points = max(0, match.away_team.tournament_points - 3)
        else:
            match.home_team.tournament_points = max(0, match.home_team.tournament_points - 1)
            match.away_team.tournament_points = max(0, match.away_team.tournament_points - 1)

        match.home_team.save()
        match.away_team.save()

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

        cleaned_data['player'] = player 
        cleaned_data['team'] = team_instance

        return cleaned_data

    def save(self, commit=True):
        event = super().save(commit=False)

        event.match = self.match
        event.player = self.cleaned_data['player']
        event.team = self.cleaned_data['team']

        if commit:
            event.full_clean()
            event.save()

        return event