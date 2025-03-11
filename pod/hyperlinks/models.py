from django.db import models
from pod.video.models import Video


class Hyperlink(models.Model):
    """Hyperlink model."""
    url = models.URLField(max_length=200)
    description = models.CharField(max_length=255, blank=True)

    def __str__(self):
        return self.url


class VideoHyperlink(models.Model):
    """Model to associate a video with a hyperlink."""
    video = models.ForeignKey(Video, on_delete=models.CASCADE, related_name='video_hyperlinks')
    hyperlink = models.ForeignKey(Hyperlink, on_delete=models.CASCADE, related_name='video_hyperlinks')

    def __str__(self):
        return f"{self.video.title} - {self.hyperlink.url}"
