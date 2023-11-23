from django.contrib import admin
from .models import Dressing
from .forms import DressingForm


class DressingAdmin(admin.ModelAdmin):
    form = DressingForm
    list_display = ("title", "watermark", "opacity", "position",
                    "opening_credits", "ending_credits")
    autocomplete_fields = [
        "owners",
        "users",
        "allow_to_groups",
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
