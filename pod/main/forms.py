from django import forms
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext_lazy as _
from django.conf import settings
from captcha.fields import CaptchaField

SUBJECT_CHOICES = getattr(
    settings,
    'SUBJECT_CHOICES', (
        ('', '-----'),
        ('info', _('Request more information')),
        ('contribute', _('Learn more about how to contribute')),
        ('request_password', _('Password request for a video')),
        ('inappropriate_content', _('Report inappropriate content')),
        ('bug', _('Correction or bug report')),
        ('other', _('Other (please specify)'))
    ))


def add_placeholder_and_asterisk(fields):
    for myField in fields:
        classname = fields[myField].widget.__class__.__name__
        if classname == 'PasswordInput' or classname == 'TextInput':
            fields[myField].widget.attrs[
                'placeholder'] = fields[myField].label
        if classname == 'CheckboxInput':
            if fields[myField].widget.attrs.get('class'):
                fields[myField].widget.attrs[
                    'class'] += ' form-check-input'
            else:
                fields[myField].widget.attrs[
                    'class'] = 'form-check-input '
        else:
            if fields[myField].required:
                fields[myField].label = mark_safe(
                    "%s <span class=\"required\">*</span>" %
                    fields[myField].label
                )
                fields[myField].widget.attrs["required"] = ""
            if fields[myField].widget.attrs.get('class'):
                fields[myField].widget.attrs[
                    'class'] += ' form-control'
            else:
                fields[myField].widget.attrs[
                    'class'] = 'form-control '
    return fields


class ContactUsForm(forms.Form):
    name = forms.CharField(label=_('Name'), required=True, max_length=512)
    email = forms.EmailField(label=_('Email'), required=True)

    subject = forms.ChoiceField(
        label=_('Subject'),
        help_text=_('Please choose a subjects related your request'),
        required=True, choices=SUBJECT_CHOICES,
        widget=forms.Select())

    description = forms.CharField(
        label=_('Description'),
        help_text=_('Provide a full description for your request'),
        widget=forms.Textarea(),
        required=True)

    captcha = CaptchaField(
        label=_('Please indicate the result of the following operation'))

    url_referrer = forms.URLField(required=False, widget=forms.HiddenInput())

    def __init__(self, request, *args, **kwargs):
        super(ContactUsForm, self).__init__(*args, **kwargs)

        if request.user and request.user.is_authenticated():
            self.fields['name'].widget = forms.HiddenInput()
            self.fields['email'].widget = forms.HiddenInput()
            self.initial['name'] = "%s" % request.user
            self.initial['email'] = "%s" % request.user.email
            # del self.fields['captcha']

        self.fields = add_placeholder_and_asterisk(self.fields)

    def clean(self):
        cleaned_data = super(ContactUsForm, self).clean()
        if cleaned_data['subject'] == '-----':
            self._errors["subject"] = self.error_class([
                _("Please specify a subject")])
        return cleaned_data
