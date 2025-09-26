from django import forms
from .models import SponsorBanner

class SponsorBannerForm(forms.ModelForm):
    class Meta:
        model = SponsorBanner
        fields = ['tournament', 'name', 'link_url', 'image']
        widgets = {
            'tournament': forms.HiddenInput(),
        }