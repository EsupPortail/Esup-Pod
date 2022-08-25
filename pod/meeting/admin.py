from django.contrib import admin
from django.contrib.sites.shortcuts import get_current_site
from django.urls import reverse
from django.utils.translation import ugettext_lazy as _
from django.utils.html import mark_safe

from .models import Meeting
from .forms import MeetingForm, MEETING_MAIN_FIELDS, get_meeting_fields


class MeetingSuperAdminForm(MeetingForm):
    is_staff = True
    is_superuser = True
    is_admin = True
    admin_form = True


class MeetingAdminForm(MeetingForm):
    is_staff = True
    is_superuser = False
    is_admin = True
    admin_form = True


@admin.register(Meeting)
class MeetingAdmin(admin.ModelAdmin):
    date_hierarchy = "updated_at"
    search_fields = ["name", "meeting_id"]
    list_display = (
        "name",
        'owner',
        "meeting_id",
        "created_at",
        "join_url",
        "is_running",  # , 'meeting_actions'
    )
    @admin.display(empty_value='')
    def join_url(self, obj):
        # <a href="{% url 'meeting:join' meeting.meeting_id meeting.get_hashkey %}" title="{% trans 'Join the meeting'%}" class="btn pod-btn-social p-1 m-0 ms-1"><i class="bi bi-link" aria-hidden="true"></i></a>
        direct_join_url = reverse('meeting:join', args=(obj.meeting_id, obj.get_hashkey()))
        link = '<a href="%s" target="_blank">%s</a>' % (direct_join_url, _("join"))
        return mark_safe(link)

    list_filter = (
        "created_at",
        'owner'
    )
    # actions = ["update_running_meetings"] if not UPDATE_RUNNING_ON_EACH_CALL else []
    list_per_page = 30
    autocomplete_fields = [
        "owner",
        "additional_owners",
        "restrict_access_to_groups",
    ]
    readonly_fields = ("meeting_id",)
    list_display_links = ("name",)

    fieldsets = (
        (None, {"fields": MEETING_MAIN_FIELDS}),
        (
            "Advanced options",
            {
                "classes": ("collapse",),
                "fields": get_meeting_fields(),
            },
        ),
    )

    # form = MeetingForm
    def get_form(self, request, obj=None, **kwargs):
        if request.user.is_superuser:
            form = MeetingSuperAdminForm
        else:
            form = MeetingAdminForm
        # form = super(MeetingAdmin, self).get_form(request, obj, **kwargs)
        return form

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if not request.user.is_superuser:
            qs = qs.filter(site=get_current_site(request))
        return qs
