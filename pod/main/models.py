from django.db import models
from django.utils.translation import ugettext_lazy as _



class LinkFooter(models.Model):
    title = models.CharField(_('Title'), max_length=250)
    order = models.PositiveSmallIntegerField(
        _('order'), default=1, blank=True, null=True)
    url = models.URLField(_('Web link'), 
    help_text=_('This field allows you to add an url.'))

    class Meta:
        ordering = ['order', 'title']
        verbose_name = _('bottom menu')
        verbose_name_plural = _('bottom menu')

    def __str__(self):
        return "%s - %s" % (self.id,self.title)

