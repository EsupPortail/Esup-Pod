from django.db import models
from django.utils.translation import ugettext_lazy as _
from django.contrib.flatpages.models import FlatPage
from django.core.exceptions import ValidationError


class LinkFooter(models.Model):
    title = models.CharField(_('Title'), max_length=250)
    order = models.PositiveSmallIntegerField(
        _('order'), default=1, blank=True, null=True)
    url = models.CharField(
        _('Web link'), blank=True, null=True, max_length=250,
        help_text=_('This field allows you to add an url.'))
    page = models.ForeignKey(
        FlatPage, blank=True, null=True,
        help_text=_('Select the page of Pod you want to link with.'))

    class Meta:
        ordering = ['order', 'title']
        verbose_name = _('bottom menu')
        verbose_name_plural = _('bottom menu')

    def __str__(self):
        return "%s - %s" % (self.id, self.title)

    def clean(self):
        if self.url is None and self.page is None:
            raise ValidationError(
                _('You must give an URL or a page to link the link'))
