from django import forms
from .models import SponsorBanner
from django.core.validators import FileExtensionValidator
from django.core.exceptions import ValidationError
from django.core.files.images import get_image_dimensions



class SponsorBannerForm(forms.ModelForm):
    MAX_IMAGE_SIZE_MB = 20
    # Input limits != Output limits
    MAX_WIDTH = 2400
    MAX_HEIGHT = 2400  
    image = forms.ImageField(
        validators=[FileExtensionValidator(['jpg', 'jpeg', 'png', 'webp'])]
    )
    class Meta:
        model = SponsorBanner
        fields = ['tournament', 'name', 'link_url', 'image']
        widgets = {
            'tournament': forms.HiddenInput(),
        }

    def clean_image(self):
        image = self.cleaned_data.get('image')

        if not image:
            return image

        # Check file size
        max_size = self.MAX_IMAGE_SIZE_MB * 1024 * 1024
        if image.size > max_size:
            raise ValidationError(
                f"Image file too large (max {self.MAX_IMAGE_SIZE_MB}MB)."
            )
        
        # Check dimensions
        width, height = get_image_dimensions(image)
        if height == 0 or width == 0:
            raise ValidationError("Invalid image")
        if width > self.MAX_WIDTH or height > self.MAX_HEIGHT:
            raise ValidationError(
                f"Image dimensions too large "
                f"(max {self.MAX_WIDTH}×{self.MAX_HEIGHT}px)."
            )

        # # Check aspect ratio
        # aspect_ratio = width / height
        # if not 2.5 <= aspect_ratio <= 4:
        #     raise ValidationError(
        #         "Banner must be wide (aspect ratio between 2.5:1 and 4:1)."
        #     )
        return image