from django.db import models
from django.conf import settings
from django.utils.translation import ugettext_lazy as _
from django.contrib.flatpages.models import FlatPage
from django.contrib.sites.models import Site
from django.core.exceptions import ValidationError
from django.template.defaultfilters import slugify
from django.dispatch import receiver
from django.db.models.signals import post_save
from django.db import connection
import os
import mimetypes
from ckeditor.fields import RichTextField


FILES_DIR = getattr(settings, "FILES_DIR", "files")

def get_nextautoincrement(model):
    cursor = connection.cursor()
    cursor.execute(
        "SELECT Auto_increment FROM information_schema.tables "
        + 'WHERE table_name="{0}" AND table_schema=DATABASE();'.format(
            model._meta.db_table
        )
    )
    row = cursor.fetchone()
    cursor.close()
    return row[0]


def get_upload_path_files(instance, filename):
    fname, dot, extension = filename.rpartition(".")
    try:
        fname.index("/")
        return os.path.join(
            FILES_DIR,
            "%s/%s.%s"
            % (
                os.path.dirname(fname),
                slugify(os.path.basename(fname)),
                extension,
            ),
        )
    except ValueError:
        return os.path.join(FILES_DIR, "%s.%s" % (slugify(fname), extension))


class CustomImageModel(models.Model):
    file = models.ImageField(
        _("Image"),
        null=True,
        upload_to=get_upload_path_files,
        blank=True,
        max_length=255,
    )

    @property
    def file_type(self):
        filetype = mimetypes.guess_type(self.file.path)[0]
        if filetype is None:
            fname, dot, extension = self.file.path.rpartition(".")
            filetype = extension.lower()
        return filetype

    file_type.fget.short_description = _("Get the file type")

    @property
    def file_size(self):
        return os.path.getsize(self.file.path)

    file_size.fget.short_description = _("Get the file size")

    @property
    def name(self):
        return os.path.basename(self.file.path)

    name.fget.short_description = _("Get the file name")

    def file_exist(self):
        return self.file and os.path.isfile(self.file.path)

    def __str__(self):
        return "%s (%s, %s)" % (self.name, self.file_type, self.file_size)


class CustomFileModel(models.Model):
    file = models.ImageField(
        _("Image"),
        null=True,
        upload_to=get_upload_path_files,
        blank=True,
        max_length=255,
    )

    @property
    def file_type(self):
        filetype = mimetypes.guess_type(self.file.path)[0]
        if filetype is None:
            fname, dot, extension = self.file.path.rpartition(".")
            filetype = extension.lower()
        return filetype

    file_type.fget.short_description = _("Get the file type")

    @property
    def file_size(self):
        return os.path.getsize(self.file.path)

    file_size.fget.short_description = _("Get the file size")

    @property
    def name(self):
        return os.path.basename(self.file.path)

    name.fget.short_description = _("Get the file name")

    def file_exist(self):
        return self.file and os.path.isfile(self.file.path)

    def __str__(self):
        return "%s (%s, %s)" % (self.name, self.file_type, self.file_size)


class LinkFooter(models.Model):
    title = models.CharField(_("Title"), max_length=250)
    order = models.PositiveSmallIntegerField(_("order"), default=1, blank=True, null=True)
    url = models.CharField(
        _("Web link"),
        blank=True,
        null=True,
        max_length=250,
        help_text=_("This field allows you to add an url."),
    )
    page = models.ForeignKey(
        FlatPage,
        blank=True,
        null=True,
        on_delete=models.CASCADE,
        help_text=_("Select the page of Pod you want to link with."),
    )
    sites = models.ManyToManyField(Site)

    class Meta:
        ordering = ["order", "title"]
        verbose_name = _("bottom menu")
        verbose_name_plural = _("bottom menu")

    def get_url(self):
        if self.url:
            return self.url
        return self.page.url

    def __str__(self):
        return "%s - %s" % (self.id, self.title)

    def clean(self):
        if self.url is None and self.page is None:
            raise ValidationError(_("You must give an URL or a page to link the link"))


@receiver(post_save, sender=LinkFooter)
def default_site_link_footer(sender, instance, created, **kwargs):
    if len(instance.sites.all()) == 0:
        instance.sites.add(Site.objects.get_current())


class Configuration(models.Model):
    key = models.SlugField(
        _("Key"),
        unique=True,
        max_length=100,
        help_text=_("Key of the configuration"),
        editable=False,
    )
    value = models.CharField(
        _("Value"), max_length=255, help_text=_("Value of the configuration")
    )
    description = models.CharField(
        _("Description"),
        max_length=255,
        help_text=_("Description of the configuration"),
        editable=False,
    )


class AdditionalChannelTab(models.Model):
    name = models.CharField(_("Value"), max_length=40, help_text=_("Name of the tab"))

    def __str__(self):
        return "%s" % (self.name)

    class Meta:
        verbose_name = _("Additional channels Tab")
        verbose_name_plural = _("Additional channel Tabs")

class Bloc(models.Model):
    """Class describing Bloc objects."""
    
    ## from pod.playlist.models import Playlist

    SLIDER = 'slider'
    SLIDER_MULTI = 'slider_multi'
    CARD_LIST = 'card_list'
    HTML = 'html'
    TYPE = (
        (SLIDER, _('Slider')),
        (SLIDER_MULTI, _('Slider multi')),
        (CARD_LIST, _('Card list')),
        (HTML, _('HTML')),
    )

    CHANNEL = 'channel'
    THEME = 'theme'
    PLAYLIST = 'playlist'
    LAST_VIDEOS = 'last_videos'
    MOST_VIEWS = 'most_views'
    EVENT_NEXT = 'event_next'
    DATA_TYPE = (
        (CHANNEL, _('Channel')),
        (THEME, _('Theme')),
        (PLAYLIST, _('Playlist')),
        (LAST_VIDEOS, _('Last videos')),
        (MOST_VIEWS, _('Most views')),
        (EVENT_NEXT, _('Event_next')),
    )

    title = models.CharField(_("Title"), max_length=250, blank=True, null=True)

    order = models.PositiveSmallIntegerField(_("order"), default=1, blank=True, null=True)

    page = models.ForeignKey(
        FlatPage,
        blank=True,
        null=True,
        on_delete=models.CASCADE,
        help_text=_("Select the page of Pod you want to link with."),
    )
    
    sites = models.ManyToManyField(Site)

    type = models.CharField(
        verbose_name=_("Type"),
        max_length=200,
        choices=TYPE,
        default=SLIDER,
        blank=True,
        null=True,
    )
    
    data_type = models.CharField(
        verbose_name=_("Data type"),
        max_length=200,
        choices=DATA_TYPE,
        default=None,
        blank=True,
        null=True,
    )

    Channel = models.ForeignKey(
        'video.Channel',
        blank=True,
        null=True,
        on_delete=models.CASCADE,
        help_text=_("Select the channel you want to link with."),
    )

    Theme = models.ForeignKey(
        'video.Theme',
        blank=True,
        null=True,
        on_delete=models.CASCADE,
        help_text=_("Select the theme you want to link with."),
    )

    Playlist = models.ForeignKey(
        'playlist.Playlist',
        blank=True,
        null=True,
        on_delete=models.CASCADE,
        help_text=_("Select the playlist you want to link with."),
    )

    html = RichTextField(
        config_name="complete",
        verbose_name=_("HTML"),
        null=True,
        blank=True,
        help_text=_("Write in html inside this field."),
    )

    display_title = models.CharField(
        verbose_name=_("Display title"),
        max_length=250,
        blank=True,
        null=True
    )
    
    no_cache = models.BooleanField(
        default=False,
        help_text=_("Check this box if you don't want to keep the cache."),
    )

    debug = models.BooleanField(
        default=False,
        help_text=_("Check this box if you want to activate debug mode."),
    )

    show_restricted = models.BooleanField(
        default=False,
        help_text=_("Check this box if you want to show restricted content."),
    )

    must_be_auth = models.BooleanField(
        verbose_name=_("Must be authenticated"),
        default=False,
        help_text=_("Check this box if users must be authenticated to view content."),
    )

    auto_slide = models.BooleanField(
        verbose_name=_("Auto slide"),
        default=True,
        help_text=_("Check this box if if you want auto slide."),
    )

    nb_element = models.PositiveIntegerField(
        verbose_name=_("Number of element"),
        default=5,
        blank=True,
        null=True
    )

    slider_multi_nb = models.PositiveIntegerField(
        verbose_name=_("Number of element for slider multi"),
        default=5,
        blank=True,
        null=True
    )

    view_videos_from_non_visible_channels = models.BooleanField(
        verbose_name=_("View videos from non visible channels"),
        default=False,
        help_text=_("Check this box if if you want view videos from non visible channels."),
    )
    
    shows_passworded= models.BooleanField(
        verbose_name=_("View videos with password"),
        default=False,
        help_text=_("Check this box if if you want view videos with password."),
    )


    def __str__(self):
        return "%s" % (self.title)

    class Meta:
        verbose_name = _("Bloc")
        verbose_name_plural = _("Blocs")

@receiver(post_save, sender=Bloc)
def default_site_bloc(sender, instance, created, **kwargs):
    if len(instance.sites.all()) == 0:
        instance.sites.add(Site.objects.get_current())
