from django import forms
from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from django.utils.translation import gettext_lazy as _
from django.contrib.sites.models import Site
from .models import Recording, Recorder
from pod.main.forms_utils import add_placeholder_and_asterisk
from django_select2 import forms as s2forms


DEFAULT_RECORDER_PATH = getattr(settings, "DEFAULT_RECORDER_PATH", "/data/ftp-pod/ftp/")
ALLOW_RECORDER_MANAGER_CHOICE_VID_OWNER = getattr(
    settings, "ALLOW_RECORDER_MANAGER_CHOICE_VID_OWNER", True
)


class RecorderWidget(s2forms.ModelSelect2Widget):
    search_fields = [
        "name__icontains",
    ]


class UserWidget(s2forms.ModelSelect2Widget):
    search_fields = [
        "username__icontains",
        "email__icontains",
        "first_name___icontains",
        "last_name__icontains",
    ]


def check_show_user(request):
    show_user = False
    if request.GET.get("recorder") and ALLOW_RECORDER_MANAGER_CHOICE_VID_OWNER:
        try:
            recorder = Recorder.objects.get(id=request.GET.get("recorder"))
            # little doubt about this condition
            if recorder and (request.user == recorder.user):
                show_user = True
        except ObjectDoesNotExist:
            pass
    return show_user


class RecordingForm(forms.ModelForm):
    def __init__(self, request, *args, **kwargs):
        super(RecordingForm, self).__init__(*args, **kwargs)

        self.fields = add_placeholder_and_asterisk(self.fields)

        if self.initial.get("type"):
            self.fields["type"].widget = forms.HiddenInput()

        self.fields["source_file"] = forms.FilePathField(
            path=DEFAULT_RECORDER_PATH, recursive=True, label=_("source_file")
        )
        self.fields["source_file"].widget.attrs["class"] = "form-control"
        self.fields["recorder"].queryset = self.fields["recorder"].queryset.filter(
            sites=Site.objects.get_current()
        )
        self.fields["user"].queryset = self.fields["user"].queryset.filter(
            owner__sites=Site.objects.get_current()
        )

        if not (
            check_show_user(request)
            or request.user.is_superuser
            or request.user.has_perm("recorder.add_recording")
        ):
            del self.fields["user"]
        if not (
            request.user.is_superuser or request.user.has_perm("recorder.add_recording")
        ):
            self.fields["recorder"].widget = forms.HiddenInput()
            self.fields["delete"].widget = forms.HiddenInput()
            self.fields["source_file"].widget = forms.HiddenInput()

    class Meta:
        model = Recording
        exclude = ("comment", "date_added")
        widgets = {"recorder": RecorderWidget, "user": UserWidget}

    delete = forms.BooleanField(
        required=False,
        label=_("Delete the record"),
        help_text=_("If checked, record will be deleted instead of saving it"),
        widget=forms.CheckboxInput(),
    )


class RecordingFileTreatmentDeleteForm(forms.Form):
    agree = forms.BooleanField(
        label=_("I agree"),
        help_text=_("Delete this record cannot be undo"),
        widget=forms.CheckboxInput(),
    )

    def __init__(self, *args, **kwargs):
        super(RecordingFileTreatmentDeleteForm, self).__init__(*args, **kwargs)
        self.fields = add_placeholder_and_asterisk(self.fields)
