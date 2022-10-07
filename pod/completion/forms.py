"""Completion forms."""
from django import forms
from django.conf import settings
from django.forms.widgets import HiddenInput

# from django.utils.translation import ugettext_lazy as _

from pod.completion.models import Contributor
from pod.completion.models import Document
from pod.completion.models import Track
from pod.completion.models import Overlay

from pod.main.forms_utils import add_placeholder_and_asterisk

FILEPICKER = False
if getattr(settings, "USE_PODFILE", False):
    FILEPICKER = True
    from pod.podfile.widgets import CustomFileWidget

USE_ENRICH_READY = getattr(settings, "USE_ENRICH_READY", False)


class ContributorForm(forms.ModelForm):
    """Contributor form fields."""

    def __init__(self, *args, **kwargs):
        """Initialize fields."""
        super(ContributorForm, self).__init__(*args, **kwargs)
        self.fields["video"].widget = HiddenInput()
        self.fields = add_placeholder_and_asterisk(self.fields)

    class Meta(object):
        """Set form Metadata."""

        model = Contributor
        fields = "__all__"


class DocumentForm(forms.ModelForm):
    """Document form fields."""

    def __init__(self, *args, **kwargs):
        """Initialize fields."""
        super(DocumentForm, self).__init__(*args, **kwargs)
        self.fields["video"].widget = HiddenInput()
        self.fields = add_placeholder_and_asterisk(self.fields)
        if FILEPICKER:
            self.fields["document"].widget = CustomFileWidget(type="file")

    class Meta(object):
        """Set form Metadata."""

        model = Document
        fields = "__all__"


class DocumentAdminForm(forms.ModelForm):
    """DocumentAdmin form fields."""

    def __init__(self, *args, **kwargs):
        """Initialize fields."""
        super(DocumentAdminForm, self).__init__(*args, **kwargs)
        if FILEPICKER:
            self.fields["document"].widget = CustomFileWidget(type="file")

    class Meta(object):
        """Set form Metadata."""

        model = Document
        fields = "__all__"


class TrackForm(forms.ModelForm):
    """Track form fields."""

    def __init__(self, *args, **kwargs):
        """Initialize fields."""
        super(TrackForm, self).__init__(*args, **kwargs)
        self.fields["video"].widget = HiddenInput()
        self.fields["src"].required = True
        self.fields = add_placeholder_and_asterisk(self.fields)
        if not USE_ENRICH_READY:
            self.fields["enrich_ready"].widget = HiddenInput()
        if FILEPICKER:
            self.fields["src"].widget = CustomFileWidget(type="file")

    class Meta(object):
        """Set form Metadata."""

        model = Track
        fields = "__all__"


class TrackAdminForm(forms.ModelForm):
    """TrackAdmin form fields."""

    def __init__(self, *args, **kwargs):
        """Initialize fields."""
        super(TrackAdminForm, self).__init__(*args, **kwargs)
        if FILEPICKER:
            self.fields["src"].widget = CustomFileWidget(type="file")

    class Meta(object):
        """Set form Metadata."""

        model = Track
        fields = "__all__"


class OverlayForm(forms.ModelForm):
    """Overlay form fields."""

    def __init__(self, *args, **kwargs):
        """Initialize fields."""
        super(OverlayForm, self).__init__(*args, **kwargs)
        self.fields["video"].widget = HiddenInput()
        self.fields["time_start"].widget.attrs["min"] = 1
        self.fields["time_end"].widget.attrs["min"] = 2
        try:
            self.fields["time_start"].widget.attrs["max"] = self.instance.video.duration
            self.fields["time_end"].widget.attrs["max"] = self.instance.video.duration
        except Exception:
            self.fields["time_start"].widget.attrs["max"] = 36000
            self.fields["time_end"].widget.attrs["max"] = 36000

        self.fields = add_placeholder_and_asterisk(self.fields)

    class Meta(object):
        """Set form Metadata."""

        model = Overlay
        fields = "__all__"
