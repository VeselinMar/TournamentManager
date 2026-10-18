import re
from django import forms
from django.utils.text import slugify
from datetime import datetime, time, date
from .models import Team, Match, Player, GoalEvent, Field, MatchEvent, Tournament
from .utils import recalculate_match_points


class TiebreakRuleOptionalMixin:
    """Older clients may not send the tie-break field; keep the stored value
    (or the model default) instead of failing validation."""

    def _make_tiebreak_optional(self):
        if 'tiebreak_rule' in self.fields:
            self.fields['tiebreak_rule'].required = False

    def clean_tiebreak_rule(self):
        value = self.cleaned_data.get('tiebreak_rule')
        if value:
            return value
        if self.instance and self.instance.pk:
            return self.instance.tiebreak_rule
        return Tournament.TIEBREAK_HEAD_TO_HEAD

class TournamentCreateForm(TiebreakRuleOptionalMixin, forms.ModelForm):
    class Meta:
        model = Tournament
        fields = ['name', 'tournament_date', 'format', 'points_for_win', 'points_for_draw', 'yellow_cards_for_suspension', 'tiebreak_rule']
        labels = {
            'points_for_win': 'Points for win',
            'points_for_draw': 'Points for draw',
            'yellow_cards_for_suspension': 'Yellow cards for suspension',
            'format': 'Tournament Format',
            'tiebreak_rule': 'Tie-break rule',
        }
        widgets = {
            'tournament_date': forms.DateInput(attrs={'type': 'date'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._make_tiebreak_optional()

    def clean(self):
        cleaned_data = super().clean()
        win = cleaned_data.get('points_for_win')
        draw = cleaned_data.get('points_for_draw')
        if win is not None and draw is not None and win <= draw:
            raise forms.ValidationError(
                "Points for win must be greater than points for draw."
            )
        threshold = cleaned_data.get('yellow_cards_for_suspension')
        if threshold is not None and threshold < 1:
            raise forms.ValidationError("Suspension threshold must be at least 1.")
        return cleaned_data

class TournamentUpdateForm(TiebreakRuleOptionalMixin, forms.ModelForm):
    class Meta:
        model = Tournament
        fields = [
            'name', 'tournament_date', 'format',
            'points_for_win', 'points_for_draw', 'yellow_cards_for_suspension', 'tiebreak_rule',
            'qualifiers_per_group', 'best_placed_qualifiers', 'third_place_match',
            'knockout_draw_resolution', 'extra_time_duration',
            'show_leaderboard', 'show_vendors', 'show_side_events', 'show_announcements',
        ]
        labels = {
            'points_for_win': 'Points for win',
            'points_for_draw': 'Points for draw',
            'yellow_cards_for_suspension': "Yellow cards for suspension",
            'show_leaderboard': 'Show leaderboard on public page',
            'show_vendors': 'Show vendors on public page',
            'show_side_events': 'Show programme on public page',
            'show_announcements': 'Show announcements on public page',
            'tiebreak_rule': 'Tie-break rule',
            'format': 'Tournament format',
            'qualifiers_per_group': 'Qualifiers per group',
            'best_placed_qualifiers': 'Extra best-placed qualifiers',
            'third_place_match': 'Play a third-place match',
            'knockout_draw_resolution': 'Knockout draws',
            'extra_time_duration': 'Extra time (minutes)',
        }
        widgets = {
            'tournament_date': forms.DateInput(attrs={'type': 'date'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._make_tiebreak_optional()
        # Settings added after the original form; older clients may not send them
        for name in ('format', 'qualifiers_per_group', 'best_placed_qualifiers',
                     'knockout_draw_resolution', 'extra_time_duration'):
            self.fields[name].required = False

        if self.instance and self.instance.pk and self.instance.matches.exists():
            # Format and bracket shape are fixed once a schedule exists
            for name in ('format', 'qualifiers_per_group', 'best_placed_qualifiers', 'third_place_match'):
                self.fields[name].disabled = True
                self.fields[name].help_text = "Reset the schedule to change this."

        # lock points fields if scored matches exist
        if self.instance and self.instance.pk:
            if self.instance.matches.filter(is_finished=True).exists():
                self.fields['points_for_win'].disabled = True
                self.fields['points_for_draw'].disabled = True
                self.fields['yellow_cards_for_suspension'].disabled = True
                self.fields['points_for_win'].help_text = (
                    "Cannot be changed after matches have been scored."
                )
                self.fields['points_for_draw'].help_text = (
                    "Cannot be changed after matches have been scored."
                )
                self.fields['yellow_cards_for_suspension'].help_text = (
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

    def _keep_when_missing(self, name):
        value = self.cleaned_data.get(name)
        if value in (None, ''):
            return getattr(self.instance, name)
        return value

    def clean_format(self):
        return self._keep_when_missing('format')

    def clean_qualifiers_per_group(self):
        return self._keep_when_missing('qualifiers_per_group')

    def clean_best_placed_qualifiers(self):
        return self._keep_when_missing('best_placed_qualifiers')

    def clean_knockout_draw_resolution(self):
        return self._keep_when_missing('knockout_draw_resolution')

    def clean_extra_time_duration(self):
        return self._keep_when_missing('extra_time_duration')
        
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

class TeamNameForm(forms.ModelForm):
    class Meta:
        model = Team
        fields = ["name"]

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

class AddPlayerForm(forms.Form):
    name = forms.CharField(max_length=100, strip=True)
    team_id = forms.IntegerField(widget=forms.HiddenInput)

    def clean(self):
        cleaned_data = super().clean()
        team_id = cleaned_data.get('team_id')
        name = cleaned_data.get('name')

        try:
            team = Team.objects.get(pk=team_id)
        except Team.DoesNotExist:
            raise forms.ValidationError("Team not found.")

        if Player.objects.filter(name__iexact=name, team=team).exists():
            raise forms.ValidationError(f"'{name}' is already on this team.")

        cleaned_data['team'] = team
        return cleaned_data

    def save(self):
        return Player.objects.create(
            name=self.cleaned_data['name'],
            team=self.cleaned_data['team']
        )

class MatchEditForm(forms.ModelForm):
    """Manual result entry. Knockout matches also take extra time / penalties."""
    extra_time = forms.BooleanField(required=False, label="Decided in extra time")
    home_penalties = forms.IntegerField(required=False, min_value=0, label="Home penalties")
    away_penalties = forms.IntegerField(required=False, min_value=0, label="Away penalties")

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
        self.conflicts = []

        if self.match:
            self.fields['home_score'].label = self.match.home_label
            self.fields['away_score'].label = self.match.away_label
            if not self.match.is_knockout:
                for name in ('extra_time', 'home_penalties', 'away_penalties'):
                    del self.fields[name]

    def clean(self):
        cleaned = super().clean()
        if self.match and self.match.is_knockout and not self.errors:
            from .competition import CompetitionError
            # Dry-run the knockout rules so errors show on the form
            home, away = cleaned.get('home_score'), cleaned.get('away_score')
            hp, ap = cleaned.get('home_penalties'), cleaned.get('away_penalties')
            if not self.match.teams_known:
                raise forms.ValidationError("Both teams must be known before entering a result.")
            if cleaned.get('extra_time') and not self.match.tournament.allows_extra_time:
                raise forms.ValidationError("This tournament goes straight to penalties.")
            if home != away and (hp is not None or ap is not None):
                raise forms.ValidationError("Penalties are only taken when the match ends in a draw.")
            if home == away and (hp is None or ap is None or hp == ap):
                raise forms.ValidationError("A drawn knockout match needs a decisive penalty result.")
        return cleaned

    def save(self, commit=True):
        match = super().save(commit=False)
        if not commit:
            return match

        if match.is_knockout:
            from .competition import apply_knockout_result
            self.conflicts = apply_knockout_result(
                match,
                self.cleaned_data['home_score'],
                self.cleaned_data['away_score'],
                self.cleaned_data.get('home_penalties'),
                self.cleaned_data.get('away_penalties'),
                bool(self.cleaned_data.get('extra_time')),
            )
            return match

        from .competition import after_group_match_finished
        stored = recalculate_match_points(
            match=match,
            new_home_score=self.cleaned_data['home_score'],
            new_away_score=self.cleaned_data['away_score'],
        )
        self.conflicts = after_group_match_finished(stored)
        return stored

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
    break_before_knockout = forms.IntegerField(
        label="Break Before Knockout Stage (minutes)",
        initial=0,
        min_value=0,
        required=False,
        help_text="Only used for Groups + Knockout tournaments.",
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


class GroupCountForm(forms.Form):
    group_count = forms.IntegerField(min_value=1, max_value=26, label="Number of groups")
