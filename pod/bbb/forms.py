from django import forms
from django.conf import settings
from .models import BBB_Meeting
from .models import Livestream
from pod.main.forms_utils import add_placeholder_and_asterisk
from django.dispatch import receiver
from django.db.models.signals import post_save
import importlib
from django.core.exceptions import ValidationError
from django.utils.translation import ugettext_lazy as _

USE_BBB = getattr(settings, "USE_BBB", False)
USE_BBB_LIVE_DOWNLOADING = getattr(settings, "USE_BBB_LIVE_DOWNLOADING", False)


class MeetingForm(forms.ModelForm):
    def __init__(self, request, *args, **kwargs):
        super(MeetingForm, self).__init__(*args, **kwargs)

        # All fields are hidden. This form is like a Confirm prompt
        self.fields = add_placeholder_and_asterisk(self.fields)
        hidden_fields = (
            "meeting_id",
            "internal_meeting_id",
            "session_date",
            "encoding_step",
            "recorded",
            "recording_available",
            "recording_url",
            "thumbnail_url",
            "encoded_by",
            "last_date_in_progress",
        )
        for field in hidden_fields:
            if self.fields.get(field, None):
                self.fields[field].widget = forms.HiddenInput()

    class Meta:
        model = BBB_Meeting
        exclude = ()


@receiver(post_save, sender=BBB_Meeting)
def launch_encode(sender, instance, created, **kwargs):
    # Useful when an administrator send a re-encode task
    if hasattr(instance, "launch_encode") and instance.launch_encode is True:
        instance.launch_encode = False
        # Re-encode is only possible when an user has already tried it
        # Re-encode is not depending on the encoding_step
        if instance.encoded_by is not None:
            mod = importlib.import_module("%s.plugins.type_%s" % (__package__, "bbb"))
            mod.process(instance)
        else:
            raise ValidationError(
                _(
                    "It is not possible to re-encode a recording "
                    "that was not originally encoded by an user."
                )
            )


class LivestreamForm(forms.ModelForm):
    def __init__(self, request, *args, **kwargs):
        super(LivestreamForm, self).__init__(*args, **kwargs)

        # All fields are hidden. This form is like a Confirm prompt
        self.fields = add_placeholder_and_asterisk(self.fields)
        hidden_fields = (
            "meeting",
            "start_date",
            "end_date",
            "status",
            "user",
            "server",
            "broadcaster_id",
            "redis_hostname",
            "redis_port",
            "redis_channel",
        )
        for field in hidden_fields:
            if self.fields.get(field, None):
                self.fields[field].widget = forms.HiddenInput()

        if not USE_BBB_LIVE_DOWNLOADING:
            self.fields["download_meeting"].widget = forms.HiddenInput()

    class Meta:
        model = Livestream
        exclude = ()
