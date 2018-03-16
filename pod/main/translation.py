from modeltranslation.translator import translator, TranslationOptions
from django.contrib.flatpages.models import FlatPage


class FlatPageTranslationOptions(TranslationOptions):
    fields = ('title', 'content',)


translator.register(FlatPage, FlatPageTranslationOptions)
