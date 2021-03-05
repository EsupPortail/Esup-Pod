from django import forms
from django.conf import settings
from .models import Meeting
from .models import Livestream
from pod.main.forms import add_placeholder_and_asterisk
from django.dispatch import receiver
from django.db.models.signals import post_save
import importlib
from django.core.exceptions import ValidationError
from django.utils.translation import ugettext_lazy as _

USE_BBB = getattr(settings, 'USE_BBB', False)
USE_BBB_LIVE_DOWNLOADING = getattr(settings, 'USE_BBB_LIVE_DOWNLOADING', False)


class MeetingForm(forms.ModelForm):

    def __init__(self, request, *args, **kwargs):
        super(MeetingForm, self).__init__(*args, **kwargs)

        # All fields are hidden. This form is like a Confirm prompt
        self.fields = add_placeholder_and_asterisk(self.fields)
        self.fields['meeting_id'].widget = forms.HiddenInput()
        self.fields['internal_meeting_id'].widget = forms.HiddenInput()
        # self.fields['meeting_name'].widget = forms.HiddenInput()
        self.fields['session_date'].widget = forms.HiddenInput()
        self.fields['encoding_step'].widget = forms.HiddenInput()
        self.fields['recorded'].widget = forms.HiddenInput()
        self.fields['recording_available'].widget = forms.HiddenInput()
        self.fields['recording_url'].widget = forms.HiddenInput()
        self.fields['thumbnail_url'].widget = forms.HiddenInput()
        self.fields['encoded_by'].widget = forms.HiddenInput()
        self.fields['last_date_in_progress'].widget = forms.HiddenInput()

    class Meta:
        model = Meeting
        exclude = ()


@receiver(post_save, sender=Meeting)
def launch_encode(sender, instance, created, **kwargs):
    # Useful when an administrator send a re-encode task
    if hasattr(instance, 'launch_encode') and instance.launch_encode is True:
        instance.launch_encode = False
        # Re-encode is only possible when an user has already tried it
        # Re-encode is not depending on the encoding_step
        if instance.encoded_by is not None:
            mod = importlib.import_module(
                '%s.plugins.type_%s' % (__package__, 'bbb'))
            mod.process(instance)
        else:
            raise ValidationError(
                _("It is not possible to re-encode a recording "
                  "that was not originally encoded by an user."))


class LivestreamForm(forms.ModelForm):

    def __init__(self, request, *args, **kwargs):
        super(LivestreamForm, self).__init__(*args, **kwargs)

        self.fields = add_placeholder_and_asterisk(self.fields)
        self.fields['meeting'].widget = forms.HiddenInput()
        self.fields['start_date'].widget = forms.HiddenInput()
        self.fields['end_date'].widget = forms.HiddenInput()
        self.fields['status'].widget = forms.HiddenInput()
        self.fields['user'].widget = forms.HiddenInput()
        self.fields['server'].widget = forms.HiddenInput()
        self.fields['broadcaster_id'].widget = forms.HiddenInput()
        self.fields['redis_hostname'].widget = forms.HiddenInput()
        self.fields['redis_port'].widget = forms.HiddenInput()
        self.fields['redis_channel'].widget = forms.HiddenInput()
        if not USE_BBB_LIVE_DOWNLOADING:
            self.fields['download_meeting'].widget = forms.HiddenInput()

    class Meta:
        model = Livestream
        exclude = ()
