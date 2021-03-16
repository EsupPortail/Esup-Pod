from django.forms import widgets
from django.utils.safestring import mark_safe
from django.template.loader import render_to_string
from django.core.exceptions import ObjectDoesNotExist

from .models import CustomFileModel, CustomImageModel


class CustomFileWidget(widgets.TextInput):

    class Media:
        js = ('podfile/js/filewidget.js',)

    def __init__(self, type=None, *args, **kwargs):
        self.type = type
        super(CustomFileWidget, self).__init__(*args, **kwargs)

    def render(self, name, value, attrs=None):
        document = None

        if value:
            try:
                if self.type == "file":
                    document = CustomFileModel.objects.get(id=value)
                else:
                    document = CustomImageModel.objects.get(id=value)

            except ObjectDoesNotExist:
                pass

        input = ('<input type="hidden" id="%(id)s" '
                 'name="%(name)s" value="%(value)s">') % {
            "id": attrs['id'] if attrs.get("id") else "",
            "name": name,
            "value": value if value else ""
        }
        template_name = 'podfile/customfilewidget.html'
        output = super(CustomFileWidget, self).render(name, value, attrs)
        return mark_safe(render_to_string(template_name, {
            'name': name,
            "id": attrs['id'] if attrs.get("id") else "",
            'value': value,
            'document': document,
            'widget': output,
            "input": input,
            "type": self.type
        }))
