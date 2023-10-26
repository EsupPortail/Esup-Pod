"""Esup-Pod podfile widgets."""
from django.forms import widgets
from django.utils.safestring import mark_safe
from django.template.loader import render_to_string
from django.core.exceptions import ObjectDoesNotExist

from .models import CustomFileModel, CustomImageModel


class CustomFileWidget(widgets.TextInput):
    class Media:
        js = ("podfile/js/filewidget.js",)

    def __init__(self, type=None, *args, **kwargs):
        self.type = type
        super(CustomFileWidget, self).__init__(*args, **kwargs)

    def render(self, name, value, attrs=None, renderer=None):
        """Render the CustomFileWidget as HTML."""

        document = None

        if value:
            try:
                if self.type == "file":
                    document = CustomFileModel.objects.get(id=value)
                else:
                    document = CustomImageModel.objects.get(id=value)

            except ObjectDoesNotExist:
                pass

        input = (
            '<input type="hidden" id="%(id)s" ' 'name="%(name)s" value="%(value)s">'
        ) % {
            "id": attrs["id"] if attrs.get("id") else "",
            "name": name,
            "value": value if value else "",
        }
        template_name = "podfile/customfilewidget.html"
        output = super(CustomFileWidget, self).render(name, value, attrs)
        context = self.get_context(name, value, attrs)
        attrs = context["widget"]["attrs"]

        # Copy all the aria-xxx attributes on button
        btn_attrs = {}
        for att_name, att_value in attrs.items():
            if "aria" in att_name:
                btn_attrs[att_name] = att_value

        return mark_safe(
            render_to_string(
                template_name,
                {
                    "name": name,
                    "id": attrs["id"] if attrs.get("id") else "",
                    "value": value,
                    "document": document,
                    "widget": output,
                    "input": input,
                    "type": self.type,
                    "attrs": attrs,
                    "btn_attrs": btn_attrs,
                },
            )
        )
