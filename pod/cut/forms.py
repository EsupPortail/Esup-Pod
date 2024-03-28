from django import forms
from .models import CutVideo


class CutVideoForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super(CutVideoForm, self).__init__(*args, **kwargs)
        self.fields["video"].widget = forms.HiddenInput()
        self.fields["duration"].widget = forms.HiddenInput()
        self.fields["start"].widget.attrs["id"] = "range1"
        self.fields["end"].widget.attrs["id"] = "range2"

    class Meta:
        model = CutVideo
        fields = ["video", "start", "end", "duration"]
        widgets = {
            "start": forms.TimeInput(
                attrs={
                    "step": "1",
                    "required": "required",
                    "size": "8",
                    "class": "text-center",
                }
            ),
            "end": forms.TimeInput(
                attrs={
                    "step": "1",
                    "required": "required",
                    "size": "8",
                    "class": "text-center",
                }
            ),
        }
