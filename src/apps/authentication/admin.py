"""
Esup-Pod - Admin configuration for the authentication app.

This module customizes the Django admin interface for User, Group, Owner,
and AccessGroup models, integrating site-specific filtering and profile extension.
"""

from django.contrib import admin
from django.contrib.admin import widgets
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import Group, User
from django.contrib.sites.models import Site
from django.contrib.sites.shortcuts import get_current_site
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _

from .forms import GroupAdminForm, GroupSiteAdminForm, OwnerAdminForm
from .models import AccessGroup, GroupSite, Owner, ServerRole

from .conf import auth_settings


class GroupSiteInline(admin.StackedInline):
    """
    Inline admin for GroupSite model, linking Groups to specific Sites.
    """

    model = GroupSite
    form = GroupSiteAdminForm
    can_delete = False
    verbose_name_plural = "groupssite"

    def get_fields(self, request, obj=None):
        """
        Dynamically filters visible fields based on user permissions.
        """
        if not request.user.is_superuser:
            exclude = ()
            exclude += ("sites",)
            self.exclude = exclude
        return list(super(GroupSiteInline, self).get_fields(request, obj))

    class Media:
        """Media."""

        css = {
            "all": (
                # "bootstrap/dist/css/bootstrap.min.css",
                # "bootstrap/css/bootstrap-grid.min.css",
                # "css/pod.css",
            )
        }
        js = (
            # "podfile/js/filewidget.js",
            # "js/main.js",
            # "bootstrap/dist/js/bootstrap.min.js",
        )


class OwnerInline(admin.StackedInline):
    """
    Inline admin for the Owner model, displayed within the User admin page.
    """

    model = Owner
    form = OwnerAdminForm
    can_delete = False
    verbose_name_plural = "owners"
    readonly_fields = ("hashkey",)

    def get_fields(self, request, obj=None):
        """
        Excludes sensitive or irrelevant fields based on the request context.
        """
        fields = list(super(OwnerInline, self).get_fields(request, obj))
        exclude_set = set()
        # obj will be None on the add page, and something on change pages
        if not obj:
            exclude_set.add("hashkey")
            exclude_set.add("auth_type")
            exclude_set.add("affiliation")
            exclude_set.add("comment")
        if not request.user.is_superuser:
            exclude_set.add("sites")
        return [f for f in fields if f not in exclude_set]

    class Media:
        """Media."""

        css = {
            "all": (
                # "bootstrap/dist/css/bootstrap.min.css",
                # "bootstrap/dist/css/bootstrap-grid.min.css",
                # "css/pod.css",
            )
        }
        js = (
            "podfile/js/filewidget.js",
            "js/main.js",
            "bootstrap/dist/js/bootstrap.min.js",
        )


class UserAdmin(BaseUserAdmin):
    """
    Custom UserAdmin that incorporates the Owner profile and site filtering.
    """

    @admin.display(description=_("Email"))
    def clickable_email(self, obj):
        """
        Returns an HTML mailto link for the user's email.
        """
        email = obj.email
        return format_html('<a href="mailto:{}">{}</a>', email, email)

    list_display = (
        "username",
        "last_name",
        "first_name",
        "clickable_email",
        "date_joined",
        "last_login",
        "is_active",
        "is_staff",
        "is_superuser",
        "owner_hashkey",
    )

    list_filter = (
        "is_staff",
        "is_superuser",
        "is_active",
        ("groups", admin.RelatedOnlyFieldListFilter),
    )
    if auth_settings.use_establishment_field:
        list_display = list_display + ("owner_establishment",)

    # readonly_fields=('is_superuser',)
    def get_readonly_fields(self, request, obj=None):
        """
        Ensures is_superuser is read-only for non-superusers.
        """
        if request.user.is_superuser:
            return []
        self.readonly_fields += ("is_superuser",)
        return self.readonly_fields

    def owner_hashkey(self, obj) -> str:
        """
        Utility method to display the owner's hashkey in the user list.
        """
        return "%s" % Owner.objects.get(user=obj).hashkey

    def formfield_for_manytomany(self, db_field, request, **kwargs):
        """
        Customizes the group selection widget and filters groups by site.
        """
        if (db_field.name) == "groups":
            kwargs["queryset"] = Group.objects.filter(
                groupsite__sites=Site.objects.get_current()
            )
        kwargs["widget"] = widgets.FilteredSelectMultiple(db_field.verbose_name, False)
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    @admin.display(description=_("Establishment"))
    def owner_establishment(self, obj) -> str:
        """
        Utility method to display the owner's establishment in the user list.
        """
        return "%s" % Owner.objects.get(user=obj).establishment

    ordering = (
        "-is_superuser",
        "username",
    )

    def get_queryset(self, request):
        """
        Filters the user list by the current site for non-superusers.
        """
        qs = super().get_queryset(request)
        if not request.user.is_superuser:
            qs = qs.filter(owner__sites=get_current_site(request))
        return qs

    def save_model(self, request, obj, form, change) -> None:
        """
        Automatically links new users to the current site on save.
        """
        super().save_model(request, obj, form, change)
        if not change:
            obj.owner.sites.add(get_current_site(request))
            obj.owner.save()

    def get_inline_instances(self, request, obj=None):
        """
        Adds the Owner inline to the User admin page.
        """
        _inlines = super().get_inline_instances(request, obj=None)
        if obj is not None:
            custom_inline = OwnerInline(self.model, self.admin_site)
            _inlines.append(custom_inline)
        return _inlines


class GroupAdmin(admin.ModelAdmin):
    """
    Custom Group admin incorporating site-specific logic and GroupSite relations.
    """

    # Use our custom form.
    form = GroupAdminForm
    # Filter permissions horizontal as well.
    filter_horizontal = ["permissions"]
    search_fields = ["name"]

    def get_queryset(self, request):
        """
        Filters groups by the current site for non-superusers.
        """
        qs = super().get_queryset(request)
        if not request.user.is_superuser:
            qs = qs.filter(groupsite__sites=get_current_site(request))
        return qs

    def save_model(self, request, obj, form, change) -> None:
        """
        Ensures new groups are linked to the current site.
        """
        super().save_model(request, obj, form, change)
        if not change:
            obj.groupsite.sites.add(get_current_site(request))
            obj.save()

    def get_inline_instances(self, request, obj=None):
        """
        Adds the GroupSite inline to the Group admin page.
        """
        _inlines = super().get_inline_instances(request, obj=None)
        if obj is not None:
            custom_inline = GroupSiteInline(self.model, self.admin_site)
            _inlines.append(custom_inline)
        return _inlines


@admin.register(AccessGroup)
class AccessGroupAdmin(admin.ModelAdmin):
    """
    Admin configuration for managing AccessGroups.
    """

    autocomplete_fields = []
    search_fields = ["id", "code_name", "display_name"]
    list_display = (
        "id",
        "code_name",
        "display_name",
        "auto_sync",
    )
    list_filter = ("auto_sync", "sites")
    filter_horizontal = ("sites",)


@admin.register(ServerRole)
class ServerRoleAdmin(admin.ModelAdmin):
    """
    Admin interface for ServerRole.
    """

    list_display = ("name", "scope", "can_delete_video", "can_edit_video")
    list_filter = ("scope", "can_delete_video", "can_edit_video")
    search_fields = ("name", "description")
    fieldsets = (
        (_("Role Information"), {"fields": ("name", "description", "scope")}),
        (
            _("Permissions (Check rights)"),
            {
                "fields": ("can_delete_video", "can_edit_video"),
                "description": _("Check the rights applicable to this role."),
            },
        ),
    )


@admin.register(Owner)
class OwnerAdmin(admin.ModelAdmin):
    """
    Admin configuration for the Owner model (usually hidden in module list).
    """

    autocomplete_fields = ["user", "accessgroups"]
    search_fields = ["user__username__icontains", "user__email__icontains"]

    def get_queryset(self, request):
        """
        Filters owners by the current site for non-superusers.
        """
        qs = super().get_queryset(request)
        if not request.user.is_superuser:
            qs = qs.filter(groupsite__sites=get_current_site(request))
        return qs

    def has_module_permission(self, request):
        """
        Hides the Owner model from the admin index module list.
        """
        return False

    class Meta:
        """Meta."""

        verbose_name = "Access group owner"


# Re-register UserAdmin
admin.site.unregister(User)
admin.site.register(User, UserAdmin)

# Register the new Group ModelAdmin instead of the original one.
admin.site.unregister(Group)
admin.site.register(Group, GroupAdmin)
