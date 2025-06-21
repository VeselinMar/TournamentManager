from django import forms
from .models import Team, Match, Player, Goal

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

        # Dynamically label the score fields using team names
        if self.match:
            self.fields['home_score'].label = self.match.home_team.name
            self.fields['away_score'].label = self.match.away_team.name

    def save(self, commit=True):
        match = super().save(commit=False)

        if not match.is_finished:
            if match.home_score > match.away_score:
                match.home_team.points += 3
            elif match.home_score < match.away_score:
                match.away_team.points += 3
            else:
                match.home_team.points += 1
                match.away_team.points += 1

            match.home_team.save()
            match.away_team.save()

        match.is_finished = True
        match.save()

        # Remove any previously assigned goals
        match.goals.all().delete()

        # Assign goals
        home_names = self.cleaned_data.get('home_scorers', '').splitlines()
        away_names = self.cleaned_data.get('away_scorers', '').splitlines()

        for name in home_names:
            name = name.strip()
            if name:
                player, _ = Player.objects.get_or_create(name=name, team=match.home_team)
                Goal.objects.create(match=match, player=player, team=match.home_team)
                player.goals += 1
                player.save()

        for name in away_names:
            name = name.strip()
            if name:
                player, _ = Player.objects.get_or_create(name=name, team=match.away_team)
                Goal.objects.create(match=match, player=player, team=match.away_team)
                player.goals += 1
                player.save()

        return match