from django.contrib.auth.models import User
from django.db import models
from django.template.defaultfilters import slugify
from django.utils.translation import ugettext as _
from pod.video.models import Video


def get_nextautoincrement(model):
    cursor = connection.cursor()
    cursor.execute(
        'SELECT Auto_increment FROM information_schema.tables ' +
        'WHERE table_name="{0}";'.format(model._meta.db_table)
    )
    row = cursor.fetchone()
    cursor.close()
    return row[0]


class Playlist(models.Model):
    title = models.CharField(_('Title'), max_length=100, unique=True)
    slug = models.SlugField(
        _('Slug'),
        unique=True,
        max_length=100,
        help_text=_('Used to access this instance, the "slug" is a short' +
                    ' label containing only letters, numbers, underscore' +
                    ' or dash top.'))
    owner = models.ForeignKey(User, verbose_name=_('Owner'))
    description = models.TextField(
        _('Description'),
        max_length=255,
        null=True,
        blank=True,
        help_text=_('Short description of the playlist.'))
    visible = models.BooleanField(
        _('Visible'),
        default=False,
        help_text=_('If checked, the playlist can be visible to users' +
                    ' other than the owner.'))

    class Meta:
        ordering = ['title', 'id']
        verbose_name = _('Playlist')
        verbose_name_plural = _('Playlists')

    def save(self, *args, **kwargs):
        newid = -1
        if not self.id:
            try:
                newid = get_nextautoincrement(Playlist)
            except Exception:
                try:
                    newid = Playlist.objects.latest('id').id
                    newid += 1
                except Exception:
                    newid = 1
        else:
            newid = self.id
        newid = '{0}'.format(newid)
        self.slug = '{0}-{1}'.format(newid, slugify(self.title))
        super(Playlist, self).save(*args, **kwargs)

    def __str__(self):
        return '{0}'.format(self.title)

    def get_first(self):
        return PlaylistElement.objects.get(playlist=self, position=1)


class PlaylistElement(models.Model):
    playlist = models.ForeignKey(Playlist, verbose_name=_('Playlist'))
    video = models.ForeignKey(Video, verbose_name=_('Video'))
    position = models.PositiveSmallIntegerField(
        _('Position'),
        default=1,
        help_text=_('Position of the video in a playlist.'))

    class Meta:
        unique_together = ('playlist', 'position',)
        ordering = ['position', 'id']
        verbose_name = _('Playlist element')
        verbose_name_plural = _('Playlist elements')
