from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.db import models
from django.template.defaultfilters import slugify
from django.utils.translation import ugettext as _
from pod.video.models import Video
from pod.main.models import get_nextautoincrement
from select2 import fields as select2_fields


class Playlist(models.Model):
    title = models.CharField(_('Title'), max_length=100, unique=True)
    slug = models.SlugField(
        _('Slug'),
        unique=True,
        max_length=100,
        help_text=_('Used to access this instance, the "slug" is a short' +
                    ' label containing only letters, numbers, underscore' +
                    ' or dash top.'))
    owner = select2_fields.ForeignKey(User, verbose_name=_('Owner'))
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

    def first(self):
        return PlaylistElement.objects.get(playlist=self, position=1)

    def last(self):
        last = PlaylistElement.objects.filter(
            playlist=self).order_by('-position')
        if last:
            return last[0].position + 1
        else:
            return 1

    def videos(self):
        videos = list()
        elements = PlaylistElement.objects.filter(playlist=self)
        for element in elements:
            videos.append(element.video)
        return videos


class PlaylistElement(models.Model):
    playlist = select2_fields.ForeignKey(Playlist, verbose_name=_('Playlist'))
    video = select2_fields.ForeignKey(Video, verbose_name=_('Video'))
    position = models.PositiveSmallIntegerField(
        _('Position'),
        default=1,
        help_text=_('Position of the video in a playlist.'))

    class Meta:
        unique_together = ('playlist', 'video',)
        ordering = ['position', 'id']
        verbose_name = _('Playlist element')
        verbose_name_plural = _('Playlist elements')

    def clean(self):
        if self.video.is_draft:
            raise ValidationError(
                _('A video in draft mode cannot be added to a playlist.'))
        if self.video.password:
            raise ValidationError(
                _('A video with a password cannot be added to a playlist.'))

    def save(self, *args, **kwargs):
        self.full_clean()
        return super(PlaylistElement, self).save(*args, **kwargs)

    def delete(self):
        elements = PlaylistElement.objects.filter(
            playlist=self.playlist, position__gt=self.position)
        for element in elements:
            element.position = element.position - 1
            element.save()
        super(PlaylistElement, self).delete()
