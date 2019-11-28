from django import forms
from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from django.utils.translation import ugettext_lazy as _

from .models import Recording, Recorder
from pod.main.forms import add_placeholder_and_asterisk

DEFAULT_RECORDER_PATH = getattr(
    settings, 'DEFAULT_RECORDER_PATH',
    "/data/ftp-pod/ftp/"
)
ALLOW_RECORDER_MANAGER_CHOICE_VID_OWNER = getattr(
    settings, "ALLOW_RECORDER_MANAGER_CHOICE_VID_OWNER", True)


def check_show_user(request):
    show_user = False
    if request.GET.get("recorder") and ALLOW_RECORDER_MANAGER_CHOICE_VID_OWNER:
        try:
            recorder = Recorder.objects.get(id=request.GET.get("recorder"))
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
            self.fields['type'].widget = forms.HiddenInput()

        self.fields['source_file'] = forms.FilePathField(
            path=DEFAULT_RECORDER_PATH,
            recursive=True,
            label=_("source_file")
        )
        self.fields['source_file'].widget.attrs['class'] = 'form-control'

        if not(check_show_user(request) or request.user.is_superuser):
            del self.fields['user']
        if not request.user.is_superuser:
            self.fields['recorder'].widget = forms.HiddenInput()
            self.fields['source_file'].widget = forms.HiddenInput()

    class Meta:
        model = Recording
        exclude = ('comment', 'date_added')
