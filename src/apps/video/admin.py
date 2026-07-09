"""
Esup-Pod - Video administrator interface.
"""

import tagulous.admin
from django.contrib import admin
from django import forms
from django.contrib import messages
from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ObjectDoesNotExist

from src.apps.video.models import (
    Video,
    Type,
    Discipline,
    Subtitle,
    Comment,
    ViewCount,
    Vote,
    Language,
    License,
    Cursus,
    VideoHyperlink,
    VideoCut,
)


class VideoHyperlinkInline(admin.TabularInline):
    """Inline admin for VideoHyperlink inside Video."""

    model = VideoHyperlink
    extra = 1
    fields = ("url", "text", "icon", "position", "time_start", "time_end")


@admin.register(Video)
class VideoAdmin(admin.ModelAdmin):
    """
    Admin interface for the Video model.
    """

    list_display = ("title", "owner", "status", "created_at", "file_size_mb")
    list_filter = ("status", "created_at", "sites")
    filter_horizontal = ("sites",)
    search_fields = ("title", "description", "owner__username", "owner__email")
    readonly_fields = ("slug", "duration", "created_at", "updated_at")

    def file_size_mb(self, obj):
        """
        Calculates and returns the file size of the video in Megabytes.
        """
        if obj.video_file and hasattr(obj.video_file, "size"):
            return f"{obj.video_file.size / (1024 * 1024):.2f} MB"
        return "N/A"

    file_size_mb.short_description = "Size (MB)"

    def has_delete_permission(self, request, obj=None):
        """
        Dynamically checks for deletion rights based on ServerRoles and Establishment.
        """
        if request.user.is_superuser:
            return True

        if obj:
            try:
                owner_profile = request.user.owner
                for role in owner_profile.server_roles.filter(can_delete_video=True):
                    if role.scope == "GLOBAL":
                        return True
                    if role.scope == "ESTABLISHMENT" and hasattr(obj.owner, "owner"):
                        if obj.owner.owner.establishment == owner_profile.establishment:
                            return True
            except ObjectDoesNotExist:
                pass

        return super().has_delete_permission(request, obj)

    def has_change_permission(self, request, obj=None):
        """
        Dynamically checks for editing rights based on ServerRoles and Establishment.
        """
        if request.user.is_superuser:
            return True

        if obj:
            try:
                owner_profile = request.user.owner
                for role in owner_profile.server_roles.filter(can_edit_video=True):
                    if role.scope == "GLOBAL":
                        return True
                    if role.scope == "ESTABLISHMENT" and hasattr(obj.owner, "owner"):
                        if obj.owner.owner.establishment == owner_profile.establishment:
                            return True
            except ObjectDoesNotExist:
                pass

        return super().has_change_permission(request, obj)


@admin.register(Type)
class TypeAdmin(admin.ModelAdmin):
    """Admin for Video Type."""

    list_display = ("title", "slug")
    search_fields = ("title",)


@admin.register(Discipline)
class DisciplineAdmin(admin.ModelAdmin):
    """Admin for Discipline."""

    list_display = ("title", "slug")
    search_fields = ("title",)


@admin.register(Subtitle)
class SubtitleAdmin(admin.ModelAdmin):
    """Admin for Subtitles."""

    list_display = ("video", "language", "file")
    list_filter = ("language",)


@admin.register(VideoHyperlink)
class VideoHyperlinkAdmin(admin.ModelAdmin):
    """Admin for VideoHyperlink."""

    list_display = ("id", "video", "text", "url", "time_start", "time_end", "created_at")
    list_filter = ("video",)
    search_fields = ("text", "url", "video__title")
    readonly_fields = ("id", "created_at", "updated_at")


@admin.register(VideoCut)
class VideoCutAdmin(admin.ModelAdmin):
    """Admin for Video Cuts."""

    list_display = ("video", "time_start", "time_end", "created_at")
    search_fields = ("video__title",)
    readonly_fields = ("id", "created_at")
    raw_id_fields = ("video",)


@admin.register(Language)
class LanguageAdmin(admin.ModelAdmin):
    """Admin for Language."""

    list_display = ("name", "slug", "order")
    search_fields = ("name", "slug")
    ordering = ("order", "name")


@admin.register(License)
class LicenseAdmin(admin.ModelAdmin):
    """Admin for License."""

    list_display = ("name", "slug", "order")
    search_fields = ("name", "slug")
    ordering = ("order", "name")


@admin.register(Cursus)
class CursusAdmin(admin.ModelAdmin):
    """Admin for Cursus."""

    list_display = ("name", "slug", "order")
    search_fields = ("name", "slug")
    ordering = ("order", "name")


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    """Admin for Comments."""

    list_display = ("id", "author", "video", "added", "parent", "direct_parent")
    list_filter = ("added",)
    search_fields = ("content", "author__username", "video__title")
    raw_id_fields = ("author", "video", "parent", "direct_parent")
    readonly_fields = ("added",)


@admin.register(ViewCount)
class ViewCountAdmin(admin.ModelAdmin):
    """Admin for Video View Counts."""

    list_display = ("video", "date", "count")
    list_filter = ("date",)
    search_fields = ("video__title",)
    raw_id_fields = ("video",)


@admin.register(Vote)
class VoteAdmin(admin.ModelAdmin):
    """Admin for Votes on Comments."""

    list_display = ("id", "user", "comment")
    search_fields = ("user__username", "comment__content")
    raw_id_fields = ("user", "comment")


# Register Tagulous dynamic tag model with custom merge to delete merged tags
@admin.register(Video.tags.tag_model)
class VideoTagAdmin(tagulous.admin.TagModelAdmin):
    """Admin for Video Tags."""

    def merge_tags(self, request, queryset):
        """
        Admin action to merge tags and delete the old ones.
        """
        is_tree = issubclass(self.model, tagulous.models.TagTreeModel)

        class MergeForm(forms.Form):
            """Form for merging tags."""

            _selected_action = forms.CharField(widget=forms.MultipleHiddenInput)
            merge_to = forms.ModelChoiceField(queryset)

        if is_tree:

            class MergeForm(MergeForm):
                """Form for merging tree tags."""

                merge_children = forms.BooleanField(required=False)

        if "merge" in request.POST:
            merge_form = MergeForm(request.POST)
            if merge_form.is_valid():
                merge_to = merge_form.cleaned_data["merge_to"]
                kwargs = {}
                if is_tree and merge_form.cleaned_data.get("merge_children"):
                    kwargs["children"] = True

                # Merge tags using tagulous
                merge_to.merge_tags(queryset, **kwargs)

                # Delete the other tags
                queryset.exclude(pk=merge_to.pk).delete()

                self.message_user(
                    request, _("Tags merged successfully"), messages.SUCCESS
                )
                return HttpResponseRedirect(request.get_full_path())

        else:
            tag_pks = request.POST.getlist(admin.helpers.ACTION_CHECKBOX_NAME)
            if len(tag_pks) < 2:
                self.message_user(
                    request,
                    _("You must select at least two tags to merge"),
                    messages.ERROR,
                )
                return HttpResponseRedirect(request.get_full_path())

            merge_form = MergeForm(
                initial={
                    admin.helpers.ACTION_CHECKBOX_NAME: request.POST.getlist(
                        admin.helpers.ACTION_CHECKBOX_NAME
                    ),
                    "merge_children": True,
                }
            )

        return render(
            request,
            "tagulous/admin/merge_tags.html",
            {
                "title": _("Merge tags"),
                "opts": self.model._meta,
                "merge_form": merge_form,
                "tags": queryset,
            },
        )
