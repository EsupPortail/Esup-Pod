from django.db import models
from django.forms import ValidationError

from django.utils.translation import gettext_lazy as _
from pod.video.models import Video
from pod.video_encode_transcript.utils import time_to_seconds


class CutVideo(models.Model):
    video = models.ForeignKey(Video, on_delete=models.CASCADE)
    start = models.TimeField(auto_now=False)
    end = models.TimeField(auto_now=False)
    duration = models.CharField(max_length=10)

    class Meta:
        verbose_name = _("Video cut")
        verbose_name_plural = _("Video cuts")

    def clean(self):
        if not self.verify_time():
            raise ValidationError(
                _("Please select values between 00:00:00 and ") + str(self.duration) + "."
            )

    def verify_time(self):
        """Check if they are the same values (to avoid unnecessary re-encoding)."""
        if CutVideo.objects.filter(video=self.video.id).exists():
            previous_cut = CutVideo.objects.get(video=self.video.id)
            if previous_cut.start == self.start and previous_cut.end == self.end:
                return False

        # Convert start and end to seconds
        try:
            start = time_to_seconds(self.start)
            end = time_to_seconds(self.end)
            duration = time_to_seconds(self.duration)
        except ValueError:
            return False
        if start < 0 or start >= end or end is None or start is None or end > duration:
            return False
        else:
            return True

    @property
    def start_in_int(self):
        return time_to_seconds(self.start)

    @property
    def end_in_int(self):
        return time_to_seconds(self.end)

    @property
    def duration_in_int(self):
        return time_to_seconds(self.duration)
