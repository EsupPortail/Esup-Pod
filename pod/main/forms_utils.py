from django import forms
from django.contrib.admin import widgets
from django.forms.utils import to_current_timezone
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext_lazy as _


class MyAdminSplitDateTime(forms.MultiWidget):
    """
    A SplitDateTime Widget that has some admin-specific styling.
    """

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


def add_placeholder_and_asterisk(fields):
    """Add placeholder and asterisk to specified fields."""
    for fieldName in fields:
        myField = fields[fieldName]
        classname = myField.widget.__class__.__name__
        if classname == "PasswordInput" or classname == "TextInput":
            myField.widget.attrs["placeholder"] = myField.label

        if classname == "CheckboxInput":
            bsClass = "form-check-input"
        elif classname == "Select":
            bsClass = "form-select"
        else:
            bsClass = "form-control"

        if myField.required:
            myField.label = mark_safe(
                '%s <span class="required_star">*</span>' % myField.label
            )
            myField.widget.attrs["required"] = ""
            myField.widget.attrs["class"] = "required " + bsClass
        else:
            myField.widget.attrs["class"] = bsClass

    return fields
