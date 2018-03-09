from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User

from authentication.models import Owner

# Define an inline admin descriptor for Employee model
# which acts a bit like a singleton
class OwnerInline(admin.StackedInline):
    model = Employee
    can_delete = False
    verbose_name_plural = 'owner'

# Define a new User admin
class UserAdmin(BaseUserAdmin):
    inlines = (OwnerInline, )

# Re-register UserAdmin
admin.site.unregister(User)
admin.site.register(User, UserAdmin)