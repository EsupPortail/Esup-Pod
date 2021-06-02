from django.contrib import admin
from django.contrib import admin
#from django.template.response import TemplateResponse
from .models import ManageVideoOwner

# Register your models here.
class ManageVideoOwnerAdmin(admin.ModelAdmin):
    change_list_template = "custom/layouts/change_video_owner/index.html"
    def changelist_view(self, request, extra_context=None):
        extra_context = extra_context or {}
        return super(ManageVideoOwnerAdmin, self).changelist_view(
                request, extra_context=extra_context)
        
    def has_add_permission(self, request, obj=None):
        return False

admin.site.register(ManageVideoOwner, ManageVideoOwnerAdmin)
