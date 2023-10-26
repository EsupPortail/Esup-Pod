from django import forms
from django.conf import settings
from django.db.models import Q
from django.utils.translation import ugettext_lazy as _
from django.contrib.admin import widgets
from pod.live.models import (
    Broadcaster,
    get_building_having_available_broadcaster,
    get_available_broadcasters_of_building,
)
from pod.live.models import Building, Event, one_hour_hence
from pod.main.forms_utils import add_placeholder_and_asterisk, MyAdminSplitDateTime
from pod.video.models import Video
from django_select2 import forms as s2forms
from django.utils import timezone
from datetime import datetime
from django.contrib import admin

USE_LIVE_TRANSCRIPTION = getattr(settings, "USE_LIVE_TRANSCRIPTION", False)
__FILEPICKER__ = False
if getattr(settings, "USE_PODFILE", False):
    __FILEPICKER__ = True
    from pod.podfile.widgets import CustomFileWidget

BROADCASTER_PILOTING_SOFTWARE = getattr(settings, "BROADCASTER_PILOTING_SOFTWARE", [])

EVENT_ACTIVE_AUTO_START = getattr(settings, "EVENT_ACTIVE_AUTO_START", False)

EVENT_GROUP_ADMIN = getattr(settings, "EVENT_GROUP_ADMIN", "event admin")


class OwnerWidget(s2forms.ModelSelect2Widget):
    search_fields = [
        "username__icontains",
        "email__icontains",
    ]


class AddOwnerWidget(s2forms.ModelSelect2MultipleWidget):
    search_fields = [
        "username__icontains",
        "email__icontains",
    ]


class AddVideoHoldWidget(s2forms.ModelSelect2Widget):
    search_fields = [
        "slug__icontains",
    ]


class BuildingAdminForm(forms.ModelForm):
    required_css_class = "required"
    is_staff = True
    is_superuser = False
    admin_form = True

    def __init__(self, *args, **kwargs):
        super(BuildingAdminForm, self).__init__(*args, **kwargs)
        if __FILEPICKER__:
            self.fields["headband"].widget = CustomFileWidget(type="image")

    def clean(self):
        super(BuildingAdminForm, self).clean()

    class Meta(object):
        model = Building
        fields = "__all__"


class BroadcasterAdminForm(forms.ModelForm):
    required_css_class = "required"

    def __init__(self, *args, **kwargs):
        super(BroadcasterAdminForm, self).__init__(*args, **kwargs)
        if __FILEPICKER__:
            self.fields["poster"].widget = CustomFileWidget(type="image")

        impl_choices = [[None, ""]]
        for val in BROADCASTER_PILOTING_SOFTWARE:
            impl_choices.append([val, val])

        self.fields["piloting_implementation"] = forms.ChoiceField(
            choices=impl_choices,
            required=False,
            label=_("Piloting implementation"),
            help_text=_("Select the piloting implementation for to this broadcaster."),
        )

    def clean(self):
        super(BroadcasterAdminForm, self).clean()

    class Meta(object):
        model = Broadcaster
        fields = "__all__"


class EventAdminForm(forms.ModelForm):
    start_date = forms.SplitDateTimeField(
        label=_("Start date"),
        initial=timezone.now,
        localize=True,
        widget=MyAdminSplitDateTime,
    )
    end_date = forms.SplitDateTimeField(
        label=_("End date"),
        initial=one_hour_hence,
        localize=True,
        widget=MyAdminSplitDateTime,
    )

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop("request", None)
        super(EventAdminForm, self).__init__(*args, **kwargs)
        self.fields["owner"].initial = self.request.user
        if __FILEPICKER__ and self.fields.get("thumbnail"):
            self.fields["thumbnail"].widget = CustomFileWidget(type="image")

    def clean(self):
        super(EventAdminForm, self).clean()
        check_event_date_and_hour(self)

    class Meta(object):
        model = Event
        fields = "__all__"
        widgets = {
            "owner": widgets.AutocompleteSelect(
                Event._meta.get_field("owner"),
                admin.site,
                attrs={"style": "width: 20em"},
            ),
            "additional_owners": widgets.AutocompleteSelectMultiple(
                Event._meta.get_field("additional_owners"),
                admin.site,
                attrs={"style": "width: 20em"},
            ),
            "restrict_access_to_groups": widgets.AutocompleteSelectMultiple(
                Event._meta.get_field("restrict_access_to_groups"),
                admin.site,
                attrs={"style": "width: 20em"},
            ),
        }


class CustomBroadcasterChoiceField(forms.ModelChoiceField):
    def label_from_instance(self, obj):
        return obj.name


def check_event_date_and_hour(form):
    if (
        "end_date" not in form.cleaned_data.keys()
        and "end_time" not in form.cleaned_data.keys()
    ):
        return

    if "start_date" in form.cleaned_data.keys():
        d_deb = form.cleaned_data["start_date"]
    else:
        d_deb = form.instance.start_date

    if "broadcaster" in form.cleaned_data.keys():
        brd = form.cleaned_data["broadcaster"]
    else:
        brd = form.instance.broadcaster

    if form.cleaned_data.get("end_time"):
        d_fin = datetime.combine(d_deb.date(), form.cleaned_data["end_time"])
        d_fin = timezone.make_aware(d_fin)
        d_fin_field = "end_time"
    else:
        d_fin = form.cleaned_data["end_date"]
        d_fin_field = "end_date"

    validate_consistency(brd, d_deb, d_fin, d_fin_field, form)


def validate_consistency(brd, d_deb, d_fin, d_fin_field, form):
    if timezone.now() >= d_fin:
        form.add_error(d_fin_field, _("End should not be in the past"))
        raise forms.ValidationError(_("An event cannot be planned in the past"))

    if d_deb >= d_fin:
        if form.cleaned_data.get("start_date"):
            form.add_error("start_date", _("Start should not be after end"))
        form.add_error(d_fin_field, _("Start should not be after end"))
        raise forms.ValidationError(_("Planification error."))

    events = Event.objects.exclude(
        (Q(end_date__lte=d_deb) | Q(start_date__gte=d_fin))
    ).filter(broadcaster_id=brd.id)

    if form.instance.id:
        events = events.exclude(id=form.instance.id)

    if events.exists():
        if form.cleaned_data.get("start_date"):
            form.add_error("start_date", _("An event is already planned at these dates"))
        else:
            form.add_error(d_fin_field, _("An event is already planned at these dates"))
        raise forms.ValidationError(_("Planification error."))


class EventPasswordForm(forms.Form):
    password = forms.CharField(label=_("Password"), widget=forms.PasswordInput())

    def __init__(self, *args, **kwargs):
        super(EventPasswordForm, self).__init__(*args, **kwargs)
        self.fields = add_placeholder_and_asterisk(self.fields)


class EventForm(forms.ModelForm):
    start_date = forms.SplitDateTimeField(
        label=_("Start date"),
        initial=timezone.now,
        localize=True,
        widget=MyAdminSplitDateTime,
    )
    end_date = forms.SplitDateTimeField(
        label=_("End date"),
        initial=one_hour_hence,
        localize=True,
        widget=MyAdminSplitDateTime,
    )
    end_time = forms.TimeField(label=_("End time"), widget=widgets.AdminDateWidget)

    fieldsets = (
        (
            None,
            {
                "fields": [
                    "title",
                    "start_date",
                    "end_date",
                    "end_time",
                    "building",
                    "broadcaster",
                    "is_draft",
                    "password",
                    "is_restricted",
                    "restrict_access_to_groups",
                ]
            },
        ),
        (
            "advanced_options",
            {
                "legend": _("Advanced options"),
                "classes": "collapse",
                "fields": [
                    "description",
                    "owner",
                    "additional_owners",
                    "type",
                    "is_auto_start",
                    "iframe_url",
                    "iframe_height",
                    "aside_iframe_url",
                    "thumbnail",
                    "video_on_hold",
                    "enable_transcription",
                ],
            },
        ),
    )
    building = forms.ModelChoiceField(
        label=_("Building"),
        queryset=Building.objects.none(),
        to_field_name="name",
        empty_label=None,
    )

    broadcaster = CustomBroadcasterChoiceField(
        label=_("Broadcaster device"),
        queryset=Broadcaster.objects.none(),
        empty_label=None,
    )

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop("user", None)
        is_current_event = kwargs.pop("is_current_event", None)
        broadcaster_id = kwargs.pop("broadcaster_id", None)
        building_id = kwargs.pop("building_id", None)
        super(EventForm, self).__init__(*args, **kwargs)
        self.auto_id = "event_%s"
        self.fields["owner"].initial = self.user
        # Manage required fields html
        self.fields = add_placeholder_and_asterisk(self.fields)
        # Manage fields to display
        self.initFields(is_current_event)

        # mise a jour dynamique de la liste des diffuseurs
        if "building" in self.data:
            self.saving()
            return

        if self.instance.pk and not is_current_event:
            self.editing()
            return

        if not self.instance.pk:
            # à la création
            self.creating(broadcaster_id, building_id)

    def creating(self, broadcaster_id, building_id):
        if broadcaster_id is not None and building_id is not None:
            query_buildings = get_building_having_available_broadcaster(
                self.user, building_id
            )
            self.fields["building"].queryset = query_buildings.all()
            self.initial["building"] = (
                Building.objects.filter(Q(id=building_id)).first().name
            )
            query_broadcaster = get_available_broadcasters_of_building(
                self.user, building_id, broadcaster_id
            )
            self.fields["broadcaster"].queryset = query_broadcaster.all()
            self.initial["broadcaster"] = broadcaster_id
        else:
            query_buildings = get_building_having_available_broadcaster(self.user)
            if query_buildings:
                self.fields["building"].queryset = query_buildings.all()
                self.initial["building"] = query_buildings.first().name
                self.fields[
                    "broadcaster"
                ].queryset = get_available_broadcasters_of_building(
                    self.user, query_buildings.first()
                )
        query_videos = Video.objects.filter(is_video=True).filter(
            Q(owner=self.user) | Q(additional_owners__in=[self.user])
        )
        self.fields["video_on_hold"].queryset = query_videos.all()

    def editing(self):
        broadcaster = self.instance.broadcaster
        self.fields["broadcaster"].queryset = get_available_broadcasters_of_building(
            self.user, broadcaster.building.id, broadcaster.id
        )
        self.fields["building"].queryset = get_building_having_available_broadcaster(
            self.user, broadcaster.building.id
        )
        self.initial["building"] = broadcaster.building.name
        query_videos = Video.objects.filter(is_video=True).filter(
            Q(owner=self.user) | Q(additional_owners__in=[self.user])
        )
        self.fields["video_on_hold"].queryset = query_videos.all()

    def saving(self):
        try:
            build = Building.objects.filter(name=self.data.get("building")).first()
            self.fields["broadcaster"].queryset = get_available_broadcasters_of_building(
                self.user, build.id
            )
            self.fields["building"].queryset = get_building_having_available_broadcaster(
                self.user, build.id
            )
            self.initial["building"] = build.name
        except (ValueError, TypeError):
            pass  # invalid input from the client;
            # ignore and fallback to empty Broadcaster queryset

    def initFields(self, is_current_event):
        if not self.user.is_superuser:
            self.remove_field("owner")
            self.instance.owner = self.user

        if (
            self.user.is_superuser
            or self.user.groups.filter(name=EVENT_GROUP_ADMIN).exists()
        ):
            self.remove_field("end_time")
        else:
            self.remove_field("end_date")
            self.fields["end_time"].widget.attrs["class"] += " vTimeField"
            self.fields["end_time"].initial = (
                timezone.localtime(self.instance.end_date).strftime("%H:%M")
                if self.instance
                else timezone.localtime(
                    self.fields["start_date"].initial + timezone.timedelta(hours=1)
                ).strftime("%H:%M")
            )

        if is_current_event:
            self.remove_field("start_date")
            self.remove_field("is_draft")
            self.remove_field("is_auto_start")
            self.remove_field("password")
            self.remove_field("is_restricted")
            self.remove_field("restrict_access_to_groups")
            self.remove_field("type")
            self.remove_field("description")
            self.remove_field("building")
            self.remove_field("broadcaster")
            self.remove_field("owner")
            self.remove_field("thumbnail")
            self.remove_field("video_on_hold")
            self.remove_field("enable_transcription")

    def remove_field(self, field):
        if self.fields.get(field):
            del self.fields[field]

    def clean(self):
        check_event_date_and_hour(self)
        cleaned_data = super(EventForm, self).clean()

        if cleaned_data.get("is_draft", False):
            cleaned_data["password"] = None
            cleaned_data["is_restricted"] = False
            cleaned_data["restrict_access_to_groups"] = []

    class Meta(object):
        model = Event
        fields = [
            "title",
            "description",
            "owner",
            "additional_owners",
            "start_date",
            "end_date",
            "end_time",
            "building",
            "broadcaster",
            "type",
            "is_draft",
            "password",
            "is_restricted",
            "restrict_access_to_groups",
            "iframe_url",
            "iframe_height",
            "aside_iframe_url",
            "video_on_hold",
        ]
        if EVENT_ACTIVE_AUTO_START:
            fields.append("is_auto_start")
        widgets = {
            "owner": OwnerWidget,
            "additional_owners": AddOwnerWidget,
            "end_time": widgets.AdminTimeWidget,
            "video_on_hold": AddVideoHoldWidget,
        }
        if __FILEPICKER__:
            fields.append("thumbnail")
            widgets["thumbnail"] = CustomFileWidget(type="image")
        if USE_LIVE_TRANSCRIPTION:
            fields.append("enable_transcription")


class EventDeleteForm(forms.Form):
    agree = forms.BooleanField(
        label=_("I agree"),
        help_text=_("Delete event cannot be undo"),
        widget=forms.CheckboxInput(),
    )

    def __init__(self, *args, **kwargs):
        super(EventDeleteForm, self).__init__(*args, **kwargs)
        self.fields = add_placeholder_and_asterisk(self.fields)


class EventImmediateForm(forms.ModelForm):
    end_date = forms.SplitDateTimeField()
    end_time = forms.TimeField(label=_("End time"), widget=widgets.AdminDateWidget)

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop("user", None)
        super(EventImmediateForm, self).__init__(*args, **kwargs)
        self.auto_id = "event_%s"
        event_date = timezone.localtime().strftime("%d/%m/%Y %H:%M")
        self.fields["title"].initial = _("Recording of %(user)s the %(date)s") % {
            "user": self.user.first_name + " " + self.user.last_name,
            "date": event_date,
        }

        # Manage required fields html
        self.fields = add_placeholder_and_asterisk(self.fields)
        # Manage fields to display
        self.initFields()

    def clean(self):
        check_event_date_and_hour(self)

    def initFields(self):
        del self.fields["end_date"]
        self.fields["end_time"].widget.attrs["class"] += " vTimeField"
        self.fields["end_time"].initial = (
            timezone.localtime(self.instance.end_date).strftime("%H:%M")
            if self.instance
            else timezone.localtime(
                self.fields["start_date"].initial + timezone.timedelta(hours=1)
            ).strftime("%H:%M")
        )

    class Meta(object):
        model = Event
        fields = [
            "title",
        ]
        hidden_fields = []
        widgets = {
            "end_time": widgets.AdminTimeWidget,
        }
