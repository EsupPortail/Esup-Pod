from django.contrib import admin
from .models import Interactive, InteractiveGroup


class InteractiveAdmin(admin.ModelAdmin):
    list_display = ("video",)


class InteractiveGroupAdmin(admin.ModelAdmin):
    list_display = ("video", "get_groups")
    # readonly_fields = ('video', )

    def get_groups(self, obj):
        return "\n".join([g.name for g in obj.groups.all()])


admin.site.register(InteractiveGroup, InteractiveGroupAdmin)
admin.site.register(Interactive, InteractiveAdmin)
