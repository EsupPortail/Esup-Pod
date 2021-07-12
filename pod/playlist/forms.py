from django import forms
from django.forms.widgets import HiddenInput
from pod.playlist.models import Playlist


class PlaylistForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super(PlaylistForm, self).__init__(*args, **kwargs)
        self.fields["owner"].widget = HiddenInput()
        for myField in self.fields:
            self.fields[myField].widget.attrs["class"] = "form-control"
        self.fields["visible"].widget.attrs["class"] = "form-check-input"

    class Meta:
        model = Playlist
        fields = ["title", "description", "visible", "owner"]
