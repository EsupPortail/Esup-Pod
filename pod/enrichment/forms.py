from django import forms
from django.conf import settings
from django.forms.widgets import HiddenInput
from django.contrib.admin import widgets
from django.utils.translation import gettext_lazy as _
from django.utils.safestring import mark_safe
from .models import Enrichment, EnrichmentGroup, EnrichmentVtt
from django.contrib.auth.models import Group
from django.contrib.sites.shortcuts import get_current_site

__FILEPICKER__ = False
if getattr(settings, "USE_PODFILE", False):
    from pod.podfile.widgets import CustomFileWidget

    __FILEPICKER__ = True


class EnrichmentAdminForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super(EnrichmentAdminForm, self).__init__(*args, **kwargs)
        if __FILEPICKER__:
            self.fields["image"].widget = CustomFileWidget(type="image")
            self.fields["document"].widget = CustomFileWidget(type="file")

    class Meta(object):
        model = Enrichment
        fields = "__all__"


class EnrichmentGroupForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super(EnrichmentGroupForm, self).__init__(*args, **kwargs)
        self.fields["groups"].widget = widgets.FilteredSelectMultiple(
            _("Groups"), False, attrs={}
        )
        self.fields["groups"].queryset = Group.objects.all().filter(
            groupsite__sites=get_current_site(None)
        )

    class Meta(object):
        model = EnrichmentGroup
        fields = ("groups",)  # '__all__'


class EnrichmentForm(forms.ModelForm):
    """Define edit forms for all enrichments types."""

    def __init__(self, *args, **kwargs):
        """Init an EnrichmentForm."""
        super(EnrichmentForm, self).__init__(*args, **kwargs)
        self.fields["video"].widget = HiddenInput()
        self.fields["start"].widget.attrs["min"] = 0
        self.fields["end"].widget.attrs["min"] = 1
        try:
            self.fields["start"].widget.attrs["max"] = self.instance.video.duration
            self.fields["end"].widget.attrs["max"] = self.instance.video.duration
        except Exception:
            self.fields["start"].widget.attrs["max"] = 36000
            self.fields["end"].widget.attrs["max"] = 36000
        for myField in self.fields:
            if self.fields[myField].required or myField == "type":
                self.fields[myField].widget.attrs["class"] = "form-control required"
                label_unicode = "{0}".format(self.fields[myField].label)
                self.fields[myField].label = mark_safe(
                    "{0} <span class='required-star'>*</span>".format(label_unicode)
                )
            else:
                self.fields[myField].widget.attrs["class"] = "form-control"
        self.fields["type"].widget.attrs["class"] = "custom-select form-select required"
        self.fields["stop_video"].widget.attrs["class"] = "form-check"
        if __FILEPICKER__:
            self.fields["image"].widget = CustomFileWidget(type="image")
            self.fields["document"].widget = CustomFileWidget(type="file")

    class Meta(object):
        model = Enrichment
        fields = "__all__"


class EnrichmentVttAdminForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super(EnrichmentVttAdminForm, self).__init__(*args, **kwargs)
        if __FILEPICKER__:
            self.fields["src"].widget = CustomFileWidget(type="file")

    class Meta(object):
        model = EnrichmentVtt
        fields = "__all__"
