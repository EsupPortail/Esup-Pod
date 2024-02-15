from modeltranslation.translator import translator, TranslationOptions
from django.contrib.flatpages.models import FlatPage
from pod.main.models import LinkFooter
from pod.main.models import Configuration
from pod.main.models import AdditionalChannelTab
from pod.main.models import Block


class FlatPageTranslationOptions(TranslationOptions):
    """Translation options for the FlatPage model."""

    fields = (
        "title",
        "content",
    )


class LinkFooterTranslationOptions(TranslationOptions):
    """Translation options for the LinkFooter model."""

    fields = ("title",)


class ConfigurationTranslationOptions(TranslationOptions):
    """Translation options for the Configuration model."""

    fields = ("description",)


class AdditionalChannelTabTranslationOptions(TranslationOptions):
    """Translation options for the AdditionalChannelTab model."""

    fields = ("name",)


class BlockTranslationOptions(TranslationOptions):
    """Translation options for the Block model."""

    fields = ("display_title",)


translator.register(FlatPage, FlatPageTranslationOptions)
translator.register(LinkFooter, LinkFooterTranslationOptions)
translator.register(Configuration, ConfigurationTranslationOptions)
translator.register(AdditionalChannelTab, AdditionalChannelTabTranslationOptions)
translator.register(Block, BlockTranslationOptions)
