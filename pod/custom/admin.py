from django.contrib import admin
from django.contrib import admin
#from django.template.response import TemplateResponse
from .models import ManageVideoOwner
from pod.custom.views import get_video_essentiels_data

# Register your models here.
class ManageVideoOwnerAdmin(admin.ModelAdmin):
    change_list_template = "custom/layouts/change_video_owner/index.html"
    def changelist_view(self, request, extra_context=None):
        extra_context = extra_context or {}
        extra_context['data'] = get_video_essentiels_data()
        return super(ManageVideoOwnerAdmin, self).changelist_view(
                request, extra_context=extra_context)




#    admin_urls = self.get_urls(admin.site.get_urls())
# admin_site = ManageVideoOwnerAdmin()
# admin.site.register(Custom, CustomAdmin)
admin.site.register(ManageVideoOwner, ManageVideoOwnerAdmin)
