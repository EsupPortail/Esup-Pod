from django.contrib import admin
from .models import Hyperlink, VideoHyperlink
from django.utils.translation import gettext as _


@admin.register(Hyperlink)
class HyperlinkAdmin(admin.ModelAdmin):
    """Hyperlink admin page."""
    list_display = ('url', 'description')
    search_fields = ('url', 'description')


@admin.register(VideoHyperlink)
class VideoHyperlinkAdmin(admin.ModelAdmin):
    """Video hyperlink admin page."""
    list_display = ('video', 'get_hyperlink_description', 'get_hyperlink_url')
    search_fields = ('video__title', 'hyperlink__description')

    def get_hyperlink_description(self, obj):
        return obj.hyperlink.description
    get_hyperlink_description.short_description = _('Hyperlink Description')

    def get_hyperlink_url(self, obj):
        return obj.hyperlink.url
    get_hyperlink_url.short_description = _('Hyperlink URL')
