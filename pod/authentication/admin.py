from django.conf import settings
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
from django.utils.translation import ugettext_lazy as _
from pod.authentication.models import Owner, GroupSite
from pod.authentication.forms import OwnerAdminForm, GroupSiteAdminForm
from django.utils.html import format_html
from django.contrib.sites.shortcuts import get_current_site
from django.contrib.auth.models import Group
from pod.authentication.forms import GroupAdminForm
from django.contrib.sites.models import Site
from django.contrib.admin import widgets
from pod.authentication.models import AccessGroup

# Define an inline admin descriptor for Owner model
# which acts a bit like a singleton

USE_ESTABLISHMENT_FIELD = getattr(settings, "USE_ESTABLISHMENT_FIELD", False)


class GroupSiteInline(admin.StackedInline):
    model = GroupSite
    form = GroupSiteAdminForm
    can_delete = False
    verbose_name_plural = "groupssite"

    def get_fields(self, request, obj=None):
        if not request.user.is_superuser:
            exclude = ()
            exclude += ("sites",)
            self.exclude = exclude
        return list(super(GroupSiteInline, self).get_fields(request, obj))

    class Media:
        css = {
            "all": (
                "bootstrap-4/css/bootstrap.min.css",
                "bootstrap-4/css/bootstrap-grid.css",
                "css/pod.css",
            )
        }
        js = (
            "podfile/js/filewidget.js",
            "js/main.js",
            "feather-icons/feather.min.js",
            "bootstrap-4/js/bootstrap.min.js",
        )


class OwnerInline(admin.StackedInline):
    model = Owner
    form = OwnerAdminForm
    can_delete = False
    verbose_name_plural = "owners"
    readonly_fields = ("hashkey",)

    def get_fields(self, request, obj=None):
        fields = list(super(OwnerInline, self).get_fields(request, obj))
        exclude_set = set()
        # obj will be None on the add page, and something on change pages
        if not obj:
            exclude_set.add("hashkey")
            exclude_set.add("auth_type")
            exclude_set.add("affiliation")
            exclude_set.add("commentaire")
        if not request.user.is_superuser:
            exclude_set.add("sites")
        return [f for f in fields if f not in exclude_set]

    class Media:
        css = {
            "all": (
                "bootstrap-4/css/bootstrap.min.css",
                "bootstrap-4/css/bootstrap-grid.css",
                "css/pod.css",
            )
        }
        js = (
            "podfile/js/filewidget.js",
            "js/main.js",
            "feather-icons/feather.min.js",
            "bootstrap-4/js/bootstrap.min.js",
        )


class UserAdmin(BaseUserAdmin):
    def clickable_email(self, obj):
        email = obj.email
        return format_html('<a href="mailto:{}">{}</a>', email, email)

    clickable_email.allow_tags = True
    clickable_email.short_description = _("Email")
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
    if USE_ESTABLISHMENT_FIELD:
        list_display = list_display + ("owner_establishment",)

    def owner_hashkey(self, obj):
        return "%s" % Owner.objects.get(user=obj).hashkey

    def formfield_for_manytomany(self, db_field, request, **kwargs):
        if (db_field.name) == "groups":
            kwargs["queryset"] = Group.objects.filter(
                groupsite__sites=Site.objects.get_current()
            )
        kwargs["widget"] = widgets.FilteredSelectMultiple(db_field.verbose_name, False)
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    def owner_establishment(self, obj):
        return "%s" % Owner.objects.get(user=obj).establishment

    owner_establishment.short_description = _("Establishment")

    ordering = (
        "-is_superuser",
        "username",
    )

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if not request.user.is_superuser:
            qs = qs.filter(owner__sites=get_current_site(request))
        return qs

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        if not change:
            obj.owner.sites.add(get_current_site(request))
            obj.owner.save()

    def get_inline_instances(self, request, obj=None):
        _inlines = super().get_inline_instances(request, obj=None)
        if obj is not None:
            custom_inline = OwnerInline(self.model, self.admin_site)
            _inlines.append(custom_inline)
        return _inlines


# Create a new Group admin.
class GroupAdmin(admin.ModelAdmin):
    # Use our custom form.
    form = GroupAdminForm
    # Filter permissions horizontal as well.
    filter_horizontal = ["permissions"]

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if not request.user.is_superuser:
            qs = qs.filter(groupsite__sites=get_current_site(request))
        return qs

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        if not change:
            obj.groupsite.sites.add(get_current_site(request))
            obj.save()

    def get_inline_instances(self, request, obj=None):
        _inlines = super().get_inline_instances(request, obj=None)
        if obj is not None:
            custom_inline = GroupSiteInline(self.model, self.admin_site)
            _inlines.append(custom_inline)
        return _inlines


class AccessGroupAdmin(admin.ModelAdmin):
    search_fields = ["id", "code_name", "display_name"]
    list_display = (
        "id",
        "code_name",
        "display_name",
    )


# Re-register UserAdmin
admin.site.unregister(User)
admin.site.register(User, UserAdmin)

# Register the new Group ModelAdmin instead of the original one.
admin.site.unregister(Group)
admin.site.register(Group, GroupAdmin)

admin.site.register(AccessGroup, AccessGroupAdmin)
