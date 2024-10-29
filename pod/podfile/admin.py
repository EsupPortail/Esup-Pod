from django.contrib import admin
from .models import CustomFileModel
from .models import CustomImageModel
from .models import UserFolder
from django.contrib.sites.shortcuts import get_current_site
from django.contrib.auth.models import User
from django.contrib.sites.models import Site
from pod.authentication.models import AccessGroup

# Register your models here.


@admin.register(UserFolder)
class UserFolderAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "owner",
    )
    list_display_links = ("name",)
    list_filter = (("owner", admin.RelatedOnlyFieldListFilter),)
    ordering = (
        "name",
        "owner",
    )
    search_fields = ["id", "name", "owner__username"]
    autocomplete_fields = ["owner", "users"]

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if (db_field.name) == "owner":
            kwargs["queryset"] = User.objects.filter(
                owner__sites=Site.objects.get_current()
            )
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    def formfield_for_manytomany(self, db_field, request, **kwargs):
        if (db_field.name) == "access_groups":
            kwargs["queryset"] = AccessGroup.objects.filter(
                sites=Site.objects.get_current()
            )
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if not request.user.is_superuser:
            qs = qs.filter(owner__owner__sites=get_current_site(request))
        return qs


@admin.register(CustomImageModel)
class CustomImageModelAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "file_type",
        "created_by",
    )
    list_display_links = ("name",)
    # list_filter = ('file_type',)
    ordering = (
        "created_by",
        "name",
    )
    readonly_fields = (
        "file_size",
        "file_type",
    )
    search_fields = ["id", "name", "created_by__username"]
    autocomplete_fields = ["folder", "created_by"]

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if not request.user.is_superuser:
            qs = qs.filter(folder__owner__owner__sites=get_current_site(request))
        return qs

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if (db_field.name) == "folder":
            kwargs["queryset"] = UserFolder.objects.filter(
                owner__owner__sites=Site.objects.get_current()
            )
        if (db_field.name) == "created_by":
            kwargs["queryset"] = User.objects.filter(
                owner__sites=Site.objects.get_current()
            )
        return super().formfield_for_foreignkey(db_field, request, **kwargs)


@admin.register(CustomFileModel)
class CustomFileModelAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "file_type",
        "created_by",
    )
    list_display_links = ("name",)
    # list_filter = ('file_type',)
    ordering = (
        "created_by",
        "name",
    )
    readonly_fields = (
        "file_size",
        "file_type",
    )
    search_fields = ["id", "name", "created_by__username"]
    autocomplete_fields = ["folder", "created_by"]

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if not request.user.is_superuser:
            qs = qs.filter(folder__owner__owner__sites=get_current_site(request))
        return qs

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if (db_field.name) == "folder":
            kwargs["queryset"] = UserFolder.objects.filter(
                owner__owner__sites=Site.objects.get_current()
            )
        if (db_field.name) == "created_by":
            kwargs["queryset"] = User.objects.filter(
                owner__sites=Site.objects.get_current()
            )
        return super().formfield_for_foreignkey(db_field, request, **kwargs)
