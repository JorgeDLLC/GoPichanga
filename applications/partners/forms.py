from django import forms
from django.forms.widgets import ClearableFileInput
from applications.field.models import Field

class FieldEditForm(forms.ModelForm):
    class Meta:
        model = Field
        fields = ['name', 'type', 'address', 'price_hour', 'has_lights']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'input'}),
            'address': forms.TextInput(attrs={'class': 'input'}),
            'price_hour': forms.NumberInput(attrs={'class': 'input', 'step': '0.10'}),
        }

# --- Widget que SÍ permite múltiples archivos ---
class MultiFileInput(ClearableFileInput):
    allow_multiple_selected = True

class AlbumUploadForm(forms.Form):
    images = forms.FileField(
        widget=MultiFileInput(attrs={'multiple': True}),
        required=False
    )
