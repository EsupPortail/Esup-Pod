from django.contrib import admin
from .models import CustomFileModel
from .models import CustomImageModel
from .models import UserFolder

# Register your models here.


class UserFolderAdmin(admin.ModelAdmin):
    list_display = ('name', 'owner',)
    list_display_links = ('name',)
    list_filter = ('owner',)
    ordering = ('name', 'owner',)
    search_fields = ['id', 'name', 'owner__username']


admin.site.register(UserFolder, UserFolderAdmin)


class CustomImageModelAdmin(admin.ModelAdmin):

    list_display = ('name', 'file_type', 'created_by',)
    list_display_links = ('name',)
    # list_filter = ('file_type',)
    ordering = ('created_by', 'name', )
    readonly_fields = ('file_size', 'file_type',)
    search_fields = ['id', 'name', 'created_by__username']


admin.site.register(CustomImageModel, CustomImageModelAdmin)


class CustomFileModelAdmin(admin.ModelAdmin):

    list_display = ('name', 'file_type', 'created_by',)
    list_display_links = ('name',)
    # list_filter = ('file_type',)
    ordering = ('created_by', 'name', )
    readonly_fields = ('file_size', 'file_type',)
    search_fields = ['id', 'name', 'created_by__username']


admin.site.register(CustomFileModel, CustomFileModelAdmin)
