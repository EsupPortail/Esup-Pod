from django.db import models
from pod.video.models import Video
from django.utils.translation import ugettext as _
from h5pp.models import h5p_contents
from django.template.defaultfilters import slugify
from django.contrib.auth.models import Group

# Create your models here.
class Interactive(models.Model):
    video = models.OneToOneField(Video, verbose_name=_('Video'),
                                 editable=False, null=True,
                                 on_delete=models.CASCADE)
    def is_interactive(self):
        return True if h5p_contents.objects.filter(slug=slugify(self.video.title)).count() > 0 else False

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

    def __str__(self):
        return "Interactive group %s" % (self.video)