"""A set of utilities for forms."""

from django_select2 import forms as s2forms
from django import forms
from django.contrib.admin import widgets
from django.forms.utils import to_current_timezone
from django.utils.safestring import mark_safe
from django.utils.translation import gettext_lazy as _


class MyAdminSplitDateTime(forms.MultiWidget):
    """A SplitDateTime Widget that has some admin-specific styling."""

    template_name = "admin/widgets/split_datetime.html"
    date_attrs = None
    time_attrs = None

    def __init__(self, attrs=None):
        adw = widgets.AdminDateWidget()
        atw = widgets.AdminTimeWidget()
        widg = [adw, atw]
        self.date_attrs = adw.attrs
        self.time_attrs = atw.attrs
        # Note that we're calling MultiWidget, not SplitDateTimeWidget, because
        # we want to define widgets.
        forms.MultiWidget.__init__(self, widg, attrs)

    def get_context(self, name, value, attrs):
        context = super().get_context(name, value, attrs)
        unique_value = ["size", "id"]
        for att in self.date_attrs:
            dattrs = context["widget"]["subwidgets"][0]["attrs"]
            val = self.date_attrs.get(att, None)
            if val and dattrs.get(att) and att not in unique_value:
                context["widget"]["subwidgets"][0]["attrs"][att] += " " + val
            else:
                context["widget"]["subwidgets"][0]["attrs"][att] = val
        for att in self.time_attrs:
            dattrs = context["widget"]["subwidgets"][1]["attrs"]
            val = self.time_attrs.get(att, None)
            if val and dattrs.get(att) and att not in unique_value:
                context["widget"]["subwidgets"][1]["attrs"][att] += " " + val
            else:
                context["widget"]["subwidgets"][1]["attrs"][att] = val
        context["date_label"] = _("Date:")
        context["time_label"] = _("Time:")
        return context

    def decompress(self, value):
        if value:
            value = to_current_timezone(value)
            return [value.date(), value.time()]
        return [None, None]


def add_describedby_attr(fields):
    """Add aria-describedby attribute to specified fields."""
    for fieldName in fields:
        my_field = fields[fieldName]
        if my_field.widget.__class__.__name__ != "HiddenInput" and my_field.help_text:
            my_field.widget.attrs["aria-describedby"] = "id_%sHelp" % fieldName
    return fields


def add_placeholder_and_asterisk(fields):
    """Add placeholder and asterisk to specified fields."""
    for fieldName in fields:
        my_field = fields[fieldName]
        classname = my_field.widget.__class__.__name__
        if classname in {"PasswordInput", "TextInput", "EmailInput", "CaptchaTextInput"}:
            my_field.widget.attrs["placeholder"] = my_field.label

        if classname in {"CheckboxInput", "CheckboxSelectMultiple"}:
            bs_class = "form-check-input"
        elif classname == "Select":
            bs_class = "form-select"
        else:
            bs_class = "form-control"

        init_class = my_field.widget.attrs.get("class", "")
        bs_class = bs_class + " " + init_class
        if my_field.required:
            my_field.label = mark_safe(
                '%s <span class="required-star">*</span>' % my_field.label
            )
            my_field.widget.attrs["required"] = ""
            my_field.widget.attrs["class"] = "required " + bs_class
        else:
            my_field.widget.attrs["class"] = bs_class

    return fields


class OwnerWidget(s2forms.ModelSelect2Widget):
    """Class OwnerWidget."""

    search_fields = [
        "username__icontains",
        "email__icontains",
    ]


class AddOwnerWidget(s2forms.ModelSelect2MultipleWidget):
    """Class AddOwnerWidget."""

    search_fields = [
        "username__icontains",
        "email__icontains",
    ]
