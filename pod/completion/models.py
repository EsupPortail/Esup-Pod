from django.db import models
from django.core.exceptions import ValidationError
from django.utils.translation import ugettext_lazy as _
from pod.video.models import Video

import base64


class Contributor(models.Model):

    ROLE_CHOICES = (
        ('actor', _('actor')),
        ('author', _('author')),
        ('designer', _('designer')),
        ('consultant', _('consultant')),
        ('contributor', _('contributor')),
        ('editor', _('editor')),
        ('speaker', _('speaker')),
        ('soundman', _('soundman')),
        ('director', _('director')),
        ('writer', _('writer')),
        ('technician', _('technician')),
        ('voice-over', _('voice-over')),
    )

    video = models.ForeignKey(Video, verbose_name=_('video'))
    name = models.CharField(_('lastname / firstname'), max_length=200)
    email_address = models.EmailField(
        _('mail'), null=True, blank=True, default='')
    role = models.CharField(
        _(u'role'), max_length=200, choices=ROLE_CHOICES, default='author')
    weblink = models.URLField(
        _(u'Web link'), max_length=200, null=True, blank=True)

    class Meta:
        verbose_name = _('Contributor')
        verbose_name_plural = _('Contributors')

    def clean(self):
        msg = list()
        msg = self.verify_attributs() + self.verify_not_same_contributor()
        if len(msg) > 0:
            raise ValidationError(msg)

    def verify_attributs(self):
        msg = list()
        if not self.name or self.name == '':
            msg.append(_('Please enter a name.'))
        elif len(self.name) < 2 or len(self.name) > 200:
            msg.append(_('Please enter a name from 2 to 200 caracters.'))
        if self.weblink and len(self.weblink) > 200:
            msg.append(
                _('You cannot enter a weblink with more than 200 caracters.'))
        if not self.role:
            msg.append(_('Please enter a role.'))
        if len(msg) > 0:
            return msg
        else:
            return list()

    def verify_not_same_contributor(self):
        msg = list()
        list_contributor = Contributor.objects.filter(video=self.video)
        if self.id:
            list_contributor = list_contributor.exclude(id=self.id)
        if len(list_contributor) > 0:
            for element in list_contributor:
                if self.name == element.name and self.role == element.role:
                    msg.append(
                        _('There is already a contributor with the same ' +
                          'name and role in the list.')
                    )
                    return msg
        return list()

    def __str__(self):
        return u'Video:{0} - Name:{1} - Role:{2}'.format(
            self.video, self.name, self.role)

    def get_base_mail(self):
        return u'{0}'.format(
            base64.b64encode(self.email_address.encode('utf-8')))

    def get_noscript_mail(self):
        return self.email_address.replace('@', "__AT__")
