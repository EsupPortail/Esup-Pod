from django.contrib import admin
from django.utils.translation import gettext_lazy as _

from .models import Follower, Following
from .tasks import task_follow, task_index_videos


@admin.register(Follower)
class FollowerAdmin(admin.ModelAdmin):
    list_display = ("actor",)


@admin.action(description=_("Send the federation request"))
def send_federation_request(modeladmin, request, queryset):
    for following in queryset:
        task_follow.delay(following.id)
    modeladmin.message_user(request, _("The federation requests have been sent"))


@admin.action(description=_("Reindex the instance videos"))
def reindex_videos(modeladmin, request, queryset):
    for following in queryset:
        task_index_videos.delay(following.id)
    modeladmin.message_user(request, _("The video indexations have started"))


@admin.register(Following)
class FollowingAdmin(admin.ModelAdmin):
    actions = [send_federation_request, reindex_videos]
    list_display = ("object", "status")
