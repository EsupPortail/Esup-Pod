from django.db import models
from django.conf import settings
from django.utils.translation import ugettext_lazy as _
from ckeditor.fields import RichTextField

if getattr(settings, 'USE_PODFILE', False):
    from pod.podfile.models import CustomImageModel
    FILEPICKER = True
else:
    FILEPICKER = False
    from pod.main.models import CustomImageModel

DEFAULT_THUMBNAIL = getattr(
    settings, 'DEFAULT_THUMBNAIL', 'img/default.png')


class Building(models.Model):
    name = models.CharField(_('name'), max_length=200, unique=True)
    headband = models.ForeignKey(CustomImageModel, models.SET_NULL,
                                 blank=True, null=True,
                                 verbose_name=_('Headband'))
    gmapurl = models.CharField(max_length=250, blank=True, null=True)

    def __str__(self):
        return self.name

    def get_headband_url(self):
        if self.headband:
            return self.headband.file.url
        else:
            thumbnail_url = ''.join(
                [
                    settings.STATIC_URL,
                    DEFAULT_THUMBNAIL])
            return thumbnail_url

    class Meta:
        verbose_name = _("Building")
        verbose_name_plural = _("Buildings")


class Broadcaster(models.Model):
    name = models.CharField(_('name'), max_length=200, unique=True)
    building = models.ForeignKey('Building', verbose_name=_('Building'))
    description = RichTextField(
        _('description'), config_name='complete', blank=True)
    poster = models.ForeignKey(
        CustomImageModel,
        models.SET_NULL,
        blank=True,
        null=True,
        verbose_name=_('Poster'))
    url = models.URLField(_('URL'), help_text=_(
        'Url of the stream'), unique=True)
    status = models.BooleanField(default=0, help_text=_(
        'Check if the broadcaster is currently sending stream.'))
    is_restricted = models.BooleanField(
        verbose_name=_(u'Restricted access'),
        help_text=_(
            'Live is accessible only to authenticated users.'),
        default=False)

    def __str__(self):
        return "%s - %s" % (self.name, self.url)

    def get_poster_url(self):
        if self.poster:
            return self.poster.file.url
        else:
            thumbnail_url = ''.join(
                [
                    settings.STATIC_URL,
                    DEFAULT_THUMBNAIL])
            return thumbnail_url

    class Meta:
        verbose_name = _("Broadcaster")
        verbose_name_plural = _("Broadcasters")
        ordering = ['building', 'name']
