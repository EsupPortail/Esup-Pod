from django_select2 import forms as s2forms
from django import forms
from django.forms.widgets import HiddenInput
from .models import Hyperlink, VideoHyperlink
from django.utils.translation import gettext as _


class HyperlinkForm(forms.ModelForm):
    """Form for creating and updating hyperlinks."""

    class Meta:
        model = Hyperlink
        fields = ["url", "description"]


class HyperlinkWidget(s2forms.ModelSelect2Widget):
    """Widget for selecting hyperlinks."""

    search_fields = [
        "url__icontains",
        "description__icontains",
    ]


class VideoHyperlinkForm(forms.ModelForm):
    """Form to associate a hyperlink with a video."""

    def __init__(self, *args, **kwargs):
        """Initialize fields."""
        super(VideoHyperlinkForm, self).__init__(*args, **kwargs)
        self.fields["video"].widget = HiddenInput()
        self.fields["hyperlink"].queryset = Hyperlink.objects.all()

    class Meta(object):
        """Set form Metadata."""

        model = VideoHyperlink
        widgets = {
            "hyperlink": HyperlinkWidget(
                attrs={
                    "data-placeholder": _("You can search hyperlink by URL or description."),
                    "class": "w-100",
                }
            )
        }
        fields = ["video", "hyperlink"]
