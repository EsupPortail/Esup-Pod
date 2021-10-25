"""Esup-Pod forms handling."""
from django import forms
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext_lazy as _
from django.conf import settings
from captcha.fields import CaptchaField

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


def add_placeholder_and_asterisk(fields):
    """Add placeholder and asterisk to specified fields."""
    for myField in fields:
        classname = fields[myField].widget.__class__.__name__
        if classname == "PasswordInput" or classname == "TextInput":
            fields[myField].widget.attrs["placeholder"] = fields[myField].label
        if classname == "CheckboxInput":
            if fields[myField].widget.attrs.get("class"):
                fields[myField].widget.attrs["class"] += " form-check-input"
            else:
                fields[myField].widget.attrs["class"] = "form-check-input "
        else:
            if fields[myField].required:
                fields[myField].label = mark_safe(
                    '%s <span class="required_star">*</span>' % fields[myField].label
                )
                fields[myField].widget.attrs["required"] = ""
            if fields[myField].widget.attrs.get("class"):
                fields[myField].widget.attrs["class"] += " form-control"
            else:
                fields[myField].widget.attrs["class"] = "form-control "
    return fields


class ContactUsForm(forms.Form):
    """Manage "Contact us" form."""

    name = forms.CharField(label=_("Name"), required=True, max_length=512)
    email = forms.EmailField(label=_("Email"), required=True)

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

<<<<<<< HEAD
        if request.user and request.user.is_authenticated:
            self.fields['name'].widget = forms.HiddenInput()
            self.fields['email'].widget = forms.HiddenInput()
            self.initial['name'] = "%s" % request.user
            self.initial['email'] = "%s" % request.user.email
=======
        if request.user and request.user.is_authenticated():
            self.fields["name"].widget = forms.HiddenInput()
            self.fields["email"].widget = forms.HiddenInput()
            self.initial["name"] = "%s" % request.user
            self.initial["email"] = "%s" % request.user.email
>>>>>>> 95782682b7c5d157bd691fca076b10627806b2fd
            # del self.fields['captcha']

        self.fields = add_placeholder_and_asterisk(self.fields)

    def clean(self):
        """Clean "contact us" form submission."""
        cleaned_data = super(ContactUsForm, self).clean()
        if "subject" in cleaned_data and cleaned_data["subject"] == "-----":
            self._errors["subject"] = self.error_class([_("Please specify a subject")])
        return cleaned_data
