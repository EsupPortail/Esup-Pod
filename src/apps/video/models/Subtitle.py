from django.db import models
from django.utils.translation import gettext_lazy as _
from .Video import Video


class Subtitle(models.Model):
    class Language(models.TextChoices):
        FRENCH = 'fr', _('French')
        ENGLISH = 'en', _('English')
        SPANISH = 'es', _('Spanish')

    video = models.ForeignKey(
        Video, related_name='subtitles', on_delete=models.CASCADE
    )
    language = models.CharField(max_length=10, choices=Language.choices, default=Language.FRENCH)
    file = models.FileField(upload_to='subtitles/')
    is_default = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.video.title} - {self.language}"
