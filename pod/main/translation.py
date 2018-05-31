from modeltranslation.translator import translator, TranslationOptions
from django.contrib.flatpages.models import FlatPage
from pod.main.models import LinkFooter


class FlatPageTranslationOptions(TranslationOptions):
    fields = ('title', 'content',)

class LinkFooterTranslationOptions(TranslationOptions):
    fields = ('title', )

translator.register(FlatPage, FlatPageTranslationOptions)
translator.register(LinkFooter, LinkFooterTranslationOptions)

