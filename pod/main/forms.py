"""Esup-Pod forms handling."""

from django import forms
from django.utils.translation import gettext_lazy as _
from django.conf import settings
from captcha.fields import CaptchaField
from .forms_utils import add_placeholder_and_asterisk
import os

SUBJECT_CHOICES = getattr(
    settings,
    "SUBJECT_CHOICES",
    (
        ("", "-----"),
        ("info", _("Request more information")),
        ("contribute", _("Learn more about how to contribute")),
        ("request_password", _("Password request for a video")),
        ("inappropriate_content", _("Report inappropriate content")),
        ("bug", _("Correction or bug report")),
        ("other", _("Other (please specify)")),
    ),
)


class DownloadFileForm(forms.Form):
    """Manage "Download File" form."""

    filename = forms.CharField(
        required=True,
    )

    def __init__(self, *args, **kwargs):
        """Init download file form."""
        super(DownloadFileForm, self).__init__(*args, **kwargs)

    def clean(self):
        """Clean "download file" form submission."""
        clean_filename = self.cleaned_data["filename"]
        fullname = os.path.join(settings.MEDIA_ROOT, clean_filename)
        dirname = os.path.dirname(fullname)
        if not os.path.isfile(clean_filename):
            raise FileNotFoundError
        elif not dirname.startswith(settings.MEDIA_ROOT):
            raise ValueError("File not in media directory")
        else:
            return self.cleaned_data


class ContactUsForm(forms.Form):
    """Manage "Contact us" form."""

    name = forms.CharField(
        label=_("Name"),
        required=True,
        max_length=512,
        widget=forms.TextInput(attrs={"autocomplete": "name"}),
    )

    email = forms.EmailField(
        label=_("Email"),
        required=True,
        widget=forms.EmailInput(attrs={"autocomplete": "email"}),
    )

    subject = forms.ChoiceField(
        label=_("Subject"),
        help_text=_("Please choose a subject related to your request"),
        required=True,
        choices=SUBJECT_CHOICES,
        widget=forms.Select(),
    )

    description = forms.CharField(
        label=_("Description"),
        help_text=_("Provide a full description for your request"),
        widget=forms.Textarea(),
        required=True,
    )

    captcha = CaptchaField(
        label=_("Please indicate the result of the following operation")
    )

    url_referrer = forms.URLField(required=False, widget=forms.HiddenInput())

    valid_human = forms.BooleanField(
        required=False,
        label=_("Check this box if you are a metal human (required)"),
        widget=forms.CheckboxInput(),
    )

    def __init__(self, request, *args, **kwargs):
        """Init contact us form."""
        super(ContactUsForm, self).__init__(*args, **kwargs)

        if request.user and request.user.is_authenticated:
            self.fields["name"].widget = forms.HiddenInput()
            self.fields["email"].widget = forms.HiddenInput()
            self.initial["name"] = "%s" % request.user
            self.initial["email"] = "%s" % request.user.email
            # del self.fields['captcha']

        self.fields = add_placeholder_and_asterisk(self.fields)

    def clean(self):
        """Clean "contact us" form submission."""
        cleaned_data = super(ContactUsForm, self).clean()
        if "subject" in cleaned_data and cleaned_data["subject"] == "-----":
            self._errors["subject"] = self.error_class([_("Please specify a subject")])
        return cleaned_data
