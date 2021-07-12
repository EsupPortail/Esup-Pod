from modeltranslation.translator import translator, TranslationOptions
from django.contrib.flatpages.models import FlatPage
from pod.main.models import LinkFooter
from pod.main.models import Configuration


class FlatPageTranslationOptions(TranslationOptions):
    fields = (
        "title",
        "content",
    )


class LinkFooterTranslationOptions(TranslationOptions):
    fields = ("title",)


class ConfigurationTranslationOptions(TranslationOptions):
    fields = ("description",)


translator.register(FlatPage, FlatPageTranslationOptions)
translator.register(LinkFooter, LinkFooterTranslationOptions)
translator.register(Configuration, ConfigurationTranslationOptions)
