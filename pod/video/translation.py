from modeltranslation.translator import translator, TranslationOptions
from django.utils.translation import ugettext_lazy as _
from pod.video.models import Channel
from pod.video.models import Theme
from pod.video.models import Type
from pod.video.models import Discipline


class TypeTranslationOptions(TranslationOptions):
    fallback_values = _('-- sorry, no translation provided --')
    fields = ('title',)
translator.register(Type, TypeTranslationOptions)


class DisciplineTranslationOptions(TranslationOptions):
    fallback_values = _('-- sorry, no translation provided --')
    fields = ('title',)
translator.register(Discipline, DisciplineTranslationOptions)


class ThemeTranslationOptions(TranslationOptions):
    fallback_values = _('-- sorry, no translation provided --')
    fields = ('title',)
translator.register(Theme, ThemeTranslationOptions)


class ChannelTranslationOptions(TranslationOptions):
    fallback_values = _('-- sorry, no translation provided --')
    fields = ('title',)
translator.register(Channel, ChannelTranslationOptions)
