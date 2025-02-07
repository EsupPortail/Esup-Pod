from modeltranslation.translator import translator, TranslationOptions
from django.utils.translation import gettext_lazy as _

from pod.video.models import Channel
from pod.video.models import Video
from pod.video.models import Theme
from pod.video.models import Type
from pod.video.models import Discipline


class TypeTranslationOptions(TranslationOptions):
    fallback_values = _("-- sorry, no translation provided --")
    fields = ("title", "description")


class DisciplineTranslationOptions(TranslationOptions):
    fallback_values = _("-- sorry, no translation provided --")
    fields = ("title", "description")


class ThemeTranslationOptions(TranslationOptions):
    # fallback_values = _('-- sorry, no translation provided --')
    fields = ("title", "description")


class ChannelTranslationOptions(TranslationOptions):
    # fallback_values = _('-- sorry, no translation provided --')
    fields = ("title", "description")


class VideoTranslationOptions(TranslationOptions):
    # fallback_values = _('-- sorry, no translation provided --')
    fields = ("title", "description")


translator.register(Channel, ChannelTranslationOptions)
translator.register(Type, TypeTranslationOptions)
translator.register(Theme, ThemeTranslationOptions)
translator.register(Discipline, DisciplineTranslationOptions)
translator.register(Video, VideoTranslationOptions)
