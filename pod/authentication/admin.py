from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
from django.utils.translation import ugettext_lazy as _
from pod.authentication.models import Owner
from pod.authentication.forms import OwnerAdminForm
from django.utils.html import format_html

from django.contrib.auth.models import Group
from pod.authentication.forms import GroupAdminForm

# Define an inline admin descriptor for Owner model
# which acts a bit like a singleton


class OwnerInline(admin.StackedInline):
    model = Owner
    form = OwnerAdminForm
    can_delete = False
    verbose_name_plural = 'owners'
    readonly_fields = ('hashkey',)

    def get_fields(self, request, obj=None):
        fields = list(super(OwnerInline, self).get_fields(request, obj))
        exclude_set = set()
        # obj will be None on the add page, and something on change pages
        if not obj:
            exclude_set.add('hashkey')
            exclude_set.add('auth_type')
            exclude_set.add('affiliation')
            exclude_set.add('commentaire')
        return [f for f in fields if f not in exclude_set]

    class Media:
        css = {
            "all": (
                'css/podfile.css',
                'bootstrap-4/css/bootstrap-grid.css',
            )
        }
        js = (
            'js/filewidget.js',
            'feather-icons/feather.min.js',
            'bootstrap-4/js/bootstrap.min.js')


class UserAdmin(BaseUserAdmin):

    def clickable_email(self, obj):
        email = obj.email
        return format_html('<a href="mailto:{}">{}</a>', email, email)

    clickable_email.allow_tags = True
    clickable_email.short_description = _('Email')
    list_display = (
        'username',
        'last_name',
        'first_name',
        'clickable_email',
        'date_joined',
        'last_login',
        'is_active',
        'is_staff',
        'is_superuser',
        'establishment',
        'owner_hashkey'
    )

    def owner_hashkey(self, obj):
        return "%s" % Owner.objects.get(user=obj).hashkey

    def establishment(self, obj):
        return "%s" % Owner.objects.get(user=obj).establishment

    ordering = ('-is_superuser', 'username', )
    inlines = (OwnerInline, )


# Create a new Group admin.
class GroupAdmin(admin.ModelAdmin):
    # Use our custom form.
    form = GroupAdminForm
    # Filter permissions horizontal as well.
    filter_horizontal = ['permissions']


# Re-register UserAdmin
admin.site.unregister(User)
admin.site.register(User, UserAdmin)

# Register the new Group ModelAdmin instead of the original one.
admin.site.unregister(Group)
admin.site.register(Group, GroupAdmin)
