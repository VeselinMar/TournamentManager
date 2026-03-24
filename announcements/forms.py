from django import forms
from .models import Announcement


class AnnouncementForm(forms.ModelForm):
    class Meta:
        model = Announcement
        fields = ['message', 'starts_at', 'ends_at', 'is_active']
        widgets = {
            'message': forms.Textarea(attrs={'rows': 3}),
            'starts_at': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'ends_at': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        starts = cleaned_data.get('starts_at')
        ends = cleaned_data.get('ends_at')
        if starts and ends and ends <= starts:
            raise forms.ValidationError("End time must be after start time.")
        return cleaned_data