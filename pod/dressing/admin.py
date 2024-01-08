from django.contrib import admin
from django.contrib.sites.shortcuts import get_current_site
from django.db.models import Q

from pod.video.models import Video
from .models import Dressing
from .forms import DressingForm


class DressingAdmin(admin.ModelAdmin):
    """Dressing admin page."""
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

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if not request.user.is_superuser:
            qs = qs.filter(groupsite__sites=get_current_site(request))
            query_videos = Video.objects.filter(is_video=True).filter(
                Q(owner=self.user) | Q(additional_owners__in=[self.user])
            )
            self.fields["opening_credits"].queryset = query_videos.all()
            self.fields["ending_credits"].queryset = query_videos.all()
        return qs

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
