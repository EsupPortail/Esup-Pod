from django.db import models
from pod.video.models import Video
from django.utils.translation import ugettext as _
from h5pp.models import h5p_contents
from django.template.defaultfilters import slugify
from django.contrib.auth.models import Group
from django.db.models.signals import pre_delete
from django.dispatch import receiver


# Create your models here.
__NAME__ = _("Interactive")


class Interactive(models.Model):
    video = models.OneToOneField(Video, verbose_name=_('Video'),
                                 editable=False, null=True,
                                 on_delete=models.CASCADE)

    @property
    def sites(self):
        return self.video.sites

    def is_interactive(self):
        return True if h5p_contents.objects.filter(
            slug=slugify(self.video.title)
        ).count() > 0 else False


@receiver(pre_delete, sender=h5p_contents,
          dispatch_uid='pre_delete-Interactive_video_removal')
def Interactive_video_removal(sender, instance, using, **kwargs):
    Interactive.objects.get(video__slug__endswith=instance.slug).delete()


class InteractiveGroup(models.Model):
    video = models.OneToOneField(Video, verbose_name=_('Video'),
                                 # editable=False, null=True,
                                 on_delete=models.CASCADE)
    groups = models.ManyToManyField(
        Group, blank=True, verbose_name=_('Groups'),
        help_text=_('Select one or more groups who'
                    ' can access to the'
                    ' enrichment of the video'))

    class Meta:
        ordering = ['video']
        verbose_name = _('Interactive Video Group')
        verbose_name_plural = _('Interactive Video Groups')

    @property
    def sites(self):
        return self.video.sites

    def __str__(self):
        return "Interactive group %s" % (self.video)
