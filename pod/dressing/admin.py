from django.contrib import admin
from .models import Dressing
from .forms import DressingAdminForm


class DressingAdmin(admin.ModelAdmin):
    """Dressing admin page."""

    def get_form(self, request, obj=None, **kwargs):
        ModelForm = super(DressingAdmin, self).get_form(request, obj, **kwargs)

        class ModelFormMetaClass(ModelForm):
            def __new__(cls, *args, **kwargs):
                kwargs["request"] = request
                return ModelForm(*args, **kwargs)

        return ModelFormMetaClass

    form = DressingAdminForm

    list_display = (
        "title",
        "watermark",
        "opacity",
        "position",
        "opening_credits",
        "ending_credits",
    )

    autocomplete_fields = [
        "opening_credits",
        "ending_credits",
    ]

    class Media:
        css = {
            "all": (
                # "bootstrap/dist/css/bootstrap.min.css",
                # "bootstrap/dist/css/bootstrap-grid.min.css",
                # "css/pod.css",
            )
        }
        js = (
            "js/main.js",
            "podfile/js/filewidget.js",
            "bootstrap/dist/js/bootstrap.min.js",
        )


admin.site.register(Dressing, DressingAdmin)
