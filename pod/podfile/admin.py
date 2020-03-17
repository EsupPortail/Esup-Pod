from django.contrib import admin
from .models import CustomFileModel
from .models import CustomImageModel
from .models import UserFolder
from django.contrib.sites.shortcuts import get_current_site

# Register your models here.


class UserFolderAdmin(admin.ModelAdmin):
    list_display = ('name', 'owner',)
    list_display_links = ('name',)
    list_filter = ('owner',)
    ordering = ('name', 'owner',)
    search_fields = ['id', 'name', 'owner__username']

    def get_search_results(self, request, queryset, search_term):
        queryset, use_distinct = super().get_search_results(
            request, queryset, search_term)
        if not request.user.is_superuser:
            queryset = queryset.filter(owner__owner__sites=get_current_site(
                request))
        return queryset, use_distinct


admin.site.register(UserFolder, UserFolderAdmin)


class CustomImageModelAdmin(admin.ModelAdmin):

    list_display = ('name', 'file_type', 'created_by',)
    list_display_links = ('name',)
    # list_filter = ('file_type',)
    ordering = ('created_by', 'name', )
    readonly_fields = ('file_size', 'file_type',)
    search_fields = ['id', 'name', 'created_by__username']

    def get_search_results(self, request, queryset, search_term):
        queryset, use_distinct = super().get_search_results(
            request, queryset, search_term)
        if not request.user.is_superuser:
            queryset = queryset.filter(
                folder__owner__owner__sites=get_current_site(
                    request))
        return queryset, use_distinct


admin.site.register(CustomImageModel, CustomImageModelAdmin)


class CustomFileModelAdmin(admin.ModelAdmin):

    list_display = ('name', 'file_type', 'created_by',)
    list_display_links = ('name',)
    # list_filter = ('file_type',)
    ordering = ('created_by', 'name', )
    readonly_fields = ('file_size', 'file_type',)
    search_fields = ['id', 'name', 'created_by__username']

    def get_search_results(self, request, queryset, search_term):
        queryset, use_distinct = super().get_search_results(
            request, queryset, search_term)
        if not request.user.is_superuser:
            queryset = queryset.filter(
                folder__owner__owner__sites=get_current_site(
                    request))
        return queryset, use_distinct


admin.site.register(CustomFileModel, CustomFileModelAdmin)
