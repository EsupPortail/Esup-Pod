"""Esup-Pod forms for the Meeting module."""

import datetime
import random
import re
import string
from collections.abc import Iterator

from django import forms
from django.conf import settings
from django.contrib.admin import widgets as admin_widgets
from django.contrib.sites.models import Site
from django.core.exceptions import ValidationError
from django.core.validators import URLValidator, validate_email
from django.db.models.query import QuerySet
from django.forms import CharField, Textarea
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from pod.main.forms_utils import (
    AddOwnerWidget,
    OwnerWidget,
    add_placeholder_and_asterisk,
)
from pod.meeting.webinar import start_webinar, stop_webinar, toggle_rtmp_gateway

from .models import InternalRecording, Meeting
from .utils import meeting_recording_disabled

__FILEPICKER__ = False
if getattr(settings, "USE_PODFILE", False):
    __FILEPICKER__ = True
    from pod.podfile.widgets import CustomFileWidget

MEETING_MAX_DURATION = getattr(settings, "MEETING_MAX_DURATION", 5)

MEETING_MAIN_FIELDS = getattr(
    settings,
    "MEETING_MAIN_FIELDS",
    (
        "name",
        "owner",
        "additional_owners",
        "attendee_password",
        "is_restricted",
        "restrict_access_to_groups",
        "slides",
    ),
)
MEETING_ACCESS_FIELDS = (
    "attendee_password",
    "is_restricted",
    "restrict_access_to_groups",
    "guest_policy",
)
MEETING_SCHEDULE_FIELDS = ("start", "start_time", "expected_duration")
MEETING_DATE_FIELDS = getattr(settings, "MEETING_DATE_FIELDS", MEETING_SCHEDULE_FIELDS)
MEETING_RECURRING_FIELDS = getattr(
    settings,
    "MEETING_RECURRING_FIELDS",
    (
        "recurrence",
        "frequency",
        "recurring_until",
        "nb_occurrences",
        "weekdays",
        "monthly_type",
    ),
)
MEETING_RECURRING_WIDGET_FIELDS = (
    "recurrence",
    "frequency",
    "recurring_until",
    "nb_occurrences",
    "days_of_week",
    "monthly_type",
)
MEETING_RECORD_OPTION_FIELDS = (
    "record",
    "auto_start_recording",
    "allow_start_stop_recording",
)
MEETING_RECORD_FIELDS = getattr(
    settings,
    "MEETING_RECORD_FIELDS",
    ("record", "auto_start_recording"),  # , "allow_start_stop_recording"
)

USE_MEETING_WEBINAR = getattr(settings, "USE_MEETING_WEBINAR", False)

MEETING_WEBINAR_FIELDS = getattr(
    settings,
    "MEETING_WEBINAR_FIELDS",
    (
        "is_webinar",
        "enable_chat",
    ),
)

__MEETING_EXCLUDE_FIELDS__ = (
    *MEETING_MAIN_FIELDS,
    *MEETING_DATE_FIELDS,
    *MEETING_RECURRING_FIELDS,
    "id",
    "start_at",
    *MEETING_RECORD_FIELDS,
    *MEETING_WEBINAR_FIELDS,
)


for field in Meeting._meta.fields:
    # print(field.name, field.editable)
    if field.editable is False:
        __MEETING_EXCLUDE_FIELDS__ = __MEETING_EXCLUDE_FIELDS__ + (field.name,)


def get_meeting_fields() -> list:
    """Get all meeting fields."""
    fields = []
    for field in Meeting._meta.fields:
        if field.name not in __MEETING_EXCLUDE_FIELDS__:
            fields.append(field.name)
    return fields


def get_random_string(length: int) -> str:
    """Get a random string, with lowercase letters."""
    # choose from all lowercase letter
    letters = string.ascii_lowercase
    result_str = "".join(random.choice(letters) for i in range(length))
    return result_str


class MeetingForm(forms.ModelForm):
    site = forms.ModelChoiceField(Site.objects.all(), required=False)
    required_css_class = "required"
    is_admin = False
    is_superuser = False
    manage_webinar = False
    is_personal = False

    def get_time_choices(
        start_time=datetime.time(0, 0, 0),
        end_time=datetime.time(23, 0, 0),
        delta=datetime.timedelta(minutes=30),
    ):
        """
        Build a choices tuple of (time object, time string) tuples.

        starting at the start time specified and ending at or before
        the end time specified in increments of size delta.

        The default is to return a choices tuple for
        9am to 5pm in 15-minute increments.
        """
        time_choices = ()
        time = start_time
        while time <= end_time:
            time_choices += ((time, time.replace(second=0, microsecond=0)),)
            # This complicated line is because you can't add
            # a timedelta object to a time object.
            time = (datetime.datetime.combine(datetime.date.today(), time) + delta).time()
        return time_choices

    def get_rounded_time():
        now = timezone.localtime(timezone.now()).time().replace(second=0, microsecond=0)
        if now.minute < 30:
            now = now.replace(minute=30)
        else:
            now = now.replace(now.hour + 1, minute=0)
        return now

    start = forms.DateField(
        label=_("Start date"),
        initial=timezone.now,
        widget=admin_widgets.AdminDateWidget,
    )
    start_time = forms.ChoiceField(
        label=_("Start time"), choices=get_time_choices(), initial=get_rounded_time
    )
    expected_duration = forms.IntegerField(
        label=_("Duration"),
        initial=2,
        max_value=MEETING_MAX_DURATION,
        min_value=1,
        help_text=_("Specify a duration in hour between 1 and %(max_duration)s hours")
        % {"max_duration": MEETING_MAX_DURATION},
    )
    field_order = ["start", "start_time", "expected_duration"]
    DAYS_OF_WEEK = [
        (0, _("Monday")),
        (1, _("Tuesday")),
        (2, _("Wednesday")),
        (3, _("Thursday")),
        (4, _("Friday")),
        (5, _("Saturday")),
        (6, _("Sunday")),
    ]

    days_of_week = forms.MultipleChoiceField(
        required=False, widget=forms.CheckboxSelectMultiple, choices=DAYS_OF_WEEK
    )
    fieldsets = (
        (
            "main_fields",
            {
                "legend": _("Main fields"),
                "icon": "bi-gear",
                "fields": tuple(
                    field
                    for field in (
                        "name",
                        "owner",
                        "additional_owners",
                        *MEETING_MAIN_FIELDS,
                    )
                    if field in MEETING_MAIN_FIELDS
                    and field
                    not in (
                        *MEETING_ACCESS_FIELDS,
                        "slides",
                        *MEETING_RECORD_OPTION_FIELDS,
                        *MEETING_SCHEDULE_FIELDS,
                    )
                ),
                "row": "main",
            },
        ),
        (
            "access_fields",
            {
                "legend": _("Access"),
                "icon": "bi-lock",
                "fields": tuple(
                    field
                    for field in MEETING_ACCESS_FIELDS
                    if field in MEETING_MAIN_FIELDS
                ),
                "row": "main",
                "right_column": True,
            },
        ),
        (
            "slides_fields",
            {
                "legend": _("Slides"),
                "icon": "bi-file-earmark",
                "fields": ("slides",) if "slides" in MEETING_MAIN_FIELDS else (),
                "row": "slides_recording",
            },
        ),
        (
            "recording_fields",
            {
                "id": "recording_fields",
                "legend": _("Record session"),
                "icon": "bi-record-circle",
                "fields": (
                    *MEETING_RECORD_FIELDS,
                    *(
                        field
                        for field in MEETING_RECORD_OPTION_FIELDS
                        if field in MEETING_MAIN_FIELDS
                    ),
                ),
                "row": "slides_recording",
                "right_column": True,
            },
        ),
        (
            "date_fields",
            {
                "legend": _("Date and time options"),
                "icon": "bi-clock-history",
                "fields": (*MEETING_SCHEDULE_FIELDS, *MEETING_DATE_FIELDS),
                "inline": True,
            },
        ),
    )
    if USE_MEETING_WEBINAR:
        fieldsets += (
            (
                "webinar_fields",
                {
                    "legend": _("Webinar options"),
                    "icon": "bi-cast",
                    "fields": MEETING_WEBINAR_FIELDS,
                },
            ),
        )

    fieldsets += (
        (
            "modal",
            {
                "legend": _("Recurring options"),
                "icon": "bi-calendar3-range",
                "id": "recurring_fields",
                "fields": tuple(
                    field for field in MEETING_RECURRING_FIELDS if field != "weekdays"
                ),
                "template": "meeting/recurring_options_modal_form.html",
            },
        ),
        (
            "advanced_options",
            {
                "legend": _("Advanced options"),
                "icon": "bi-file-earmark-plus-fill",
                "collapse": True,
                "fields": get_meeting_fields(),
            },
        ),
    )
    advanced_fieldsets = (
        {
            "id": "advanced_general",
            "legend": _("General settings"),
            "icon": "bi-gear",
            "row": "advanced_general_access",
        },
        {
            "id": "advanced_access",
            "legend": _("Access"),
            "icon": "bi-lock",
            "row": "advanced_general_access",
            "right_column": True,
            "fields": ("max_participants", *MEETING_ACCESS_FIELDS),
        },
        {
            "id": "advanced_restrictions",
            "legend": _("Restrictions"),
            "icon": "bi-shield-lock",
            "row": "advanced_restrictions_technical",
            "fields": (
                "webcam_only_for_moderators",
                "lock_settings_disable_cam",
                "lock_settings_disable_mic",
                "lock_settings_disable_private_chat",
                "lock_settings_disable_public_chat",
                "lock_settings_disable_note",
                "lock_settings_locked_layout",
            ),
        },
        {
            "id": "advanced_technical",
            "legend": _("Technical settings"),
            "icon": "bi-tools",
            "row": "advanced_restrictions_technical",
            "right_column": True,
            "fields": ("parent_meeting_id", "voice_bridge"),
        },
        {
            "id": "advanced_recording",
            "legend": _("Record session"),
            "icon": "bi-record-circle",
            "fields": MEETING_RECORD_OPTION_FIELDS,
        },
    )

    def group_advanced_fields(self, fields: list[forms.BoundField]) -> list[dict]:
        """Group the available advanced fields, keeping extra fields in general settings."""
        group_by_field = {
            name: group["id"]
            for group in self.advanced_fieldsets
            for name in group.get("fields", ())
        }
        grouped_fields = {group["id"]: [] for group in self.advanced_fieldsets}
        for field in fields:
            grouped_fields[group_by_field.get(field.name, "advanced_general")].append(
                field
            )
        return [
            {**group, "fields": grouped_fields[group["id"]]}
            for group in self.advanced_fieldsets
            if grouped_fields[group["id"]]
        ]

    def visible_fieldsets(self) -> Iterator[dict]:
        """Yield nonempty fieldsets with each visible field rendered once."""
        # The recurrence modal already renders its standard widgets.
        fields = {
            field.name: field
            for field in self.visible_fields()
            if field.name not in MEETING_RECURRING_WIDGET_FIELDS
        }
        for name, options in self.fieldsets:
            fieldset_fields = [
                fields.pop(field_name)
                for field_name in options["fields"]
                if field_name in fields
            ]
            if fieldset_fields or options.get("template"):
                fieldset = {
                    **options,
                    "id": options.get("id", name),
                    "fields": fieldset_fields,
                }
                if options.get("collapse"):
                    fieldset["expanded"] = any(field.errors for field in fieldset_fields)
                    fieldset["groups"] = self.group_advanced_fields(fieldset_fields)
                yield fieldset

    def filter_fields_admin(form) -> None:
        """Remove fields for not admin user."""
        if form.is_superuser is False and form.is_admin is False:
            form.remove_field("owner")

        if not hasattr(form, "admin_form"):
            form.remove_field("site")
        else:
            form.remove_field("days_of_week")

    def filter_fields_webinar(form) -> None:
        """Display webinar fields only for authorized user."""
        if (
            form.manage_webinar is False
            and form.is_admin is False
            and form.is_superuser is False
        ) or (form.is_personal):
            form.remove_field("is_webinar")
            form.remove_field("enable_chat")

    def clean_start_date(self) -> None:
        """Check two things about start date.

        - the start date is before the recurrence deadline.
        - in the case of weekly recurrence, the start day must be selected from the list of weekdays.
        The function raise a validation error if a condition is not met.
        """
        if (
            "start" in self.cleaned_data.keys()
            and "recurring_until" in self.cleaned_data.keys()
            and self.cleaned_data["recurring_until"] is not None
            and (self.cleaned_data["start"] > self.cleaned_data["recurring_until"])
        ):
            raise ValidationError(_("Start date must be less than recurring until date"))

        if (
            self.cleaned_data.get("weekdays")
            and self.cleaned_data.get("start")
            and self.cleaned_data.get("recurrence") == "weekly"
            and (
                str(self.cleaned_data.get("start").weekday())
                not in self.cleaned_data.get("weekdays")
            )
        ):
            raise ValidationError(
                _(
                    "In case of weekly recurring, the day of the start date must be selected."
                )
            )

        if not self.cleaned_data.get("recurring_until"):
            self.instance.recurring_until = None
            self.instance.nb_occurrences = None

    def clean_add_owner(self):
        """Check if meeting owner not in additional owners."""
        if "additional_owners" in self.cleaned_data.keys() and isinstance(
            self.cleaned_data["additional_owners"], QuerySet
        ):
            meetingowner = (
                self.instance.owner
                if hasattr(self.instance, "owner")
                else (
                    self.cleaned_data["owner"]
                    if "owner" in self.cleaned_data.keys()
                    else self.current_user
                )
            )
            if (
                meetingowner
                and meetingowner in self.cleaned_data["additional_owners"].all()
            ):
                raise ValidationError(
                    _("Owner of the video cannot be an additional owner too")
                )

    def clean(self):
        """Clean all form fields."""
        self.cleaned_data = super(MeetingForm, self).clean()
        if "expected_duration" in self.cleaned_data.keys():
            self.cleaned_data["expected_duration"] = timezone.timedelta(
                hours=self.cleaned_data["expected_duration"]
            )

        if "days_of_week" in self.cleaned_data.keys():
            tab = self.cleaned_data["days_of_week"]
            self.cleaned_data["weekdays"] = "".join(tab)

        self.clean_start_date()

        self.clean_add_owner()
        if (
            "restrict_access_to_groups" in self.cleaned_data.keys()
            and len(self.cleaned_data["restrict_access_to_groups"]) > 0
        ):
            self.cleaned_data["is_restricted"] = True

        if (
            "start_time" in self.cleaned_data.keys()
            and "start" in self.cleaned_data.keys()
        ):
            start_time = datetime.datetime.strptime(
                self.cleaned_data["start_time"], "%H:%M:%S"
            ).time()
            start_datetime = datetime.datetime.combine(
                self.cleaned_data["start"], start_time
            )
            start_datetime = timezone.make_aware(start_datetime)
            self.instance.start_at = start_datetime

        if "voice_bridge" in self.cleaned_data.keys() and self.cleaned_data[
            "voice_bridge"
        ] not in range(10000, 99999):
            raise ValidationError(
                _("Voice bridge must be a 5-digit number in the range 10000 to 99999")
            )
        # Manage when user has changed webinar fields
        self.is_webinar_has_changed()
        self.enable_chat_has_changed()

    def is_webinar_has_changed(self):
        """Manage when user has changed is_webinar field and disable the webinar mode."""
        if self.instance.pk is not None and "is_webinar" in self.cleaned_data:
            if self.instance.is_webinar != self.cleaned_data["is_webinar"]:
                # Disable webinar mode when meeting running
                if (
                    self.instance.get_is_meeting_running() is True
                    and self.cleaned_data["is_webinar"] is False
                ):
                    # Stop the webinar in this case
                    stop_webinar(self.request, self.instance.id)
                # Enable webinar mode when meeting running and owner
                if (
                    self.instance.get_is_meeting_running() is True
                    and self.cleaned_data["is_webinar"] is True
                    and self.instance.owner == self.request.user
                ):
                    # Start the webinar in this case
                    start_webinar(self.request, self.instance.id)

    def enable_chat_has_changed(self):
        """Manage when user has changed enable_chat field."""
        if self.instance.pk is not None and "enable_chat" in self.cleaned_data:
            if self.instance.enable_chat != self.cleaned_data["enable_chat"]:
                if self.instance.get_is_meeting_running() is True:
                    # When enable chat field changed, send a toggle request
                    # to SIPMediaGW if webinar already started
                    toggle_rtmp_gateway(self.instance.id)

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop("request", None)
        self.is_staff = (
            kwargs.pop("is_staff") if "is_staff" in kwargs.keys() else self.is_staff
        )

        self.is_superuser = (
            kwargs.pop("is_superuser")
            if ("is_superuser" in kwargs.keys())
            else self.is_superuser
        )
        self.current_lang = kwargs.pop("current_lang", settings.LANGUAGE_CODE)
        self.current_user = kwargs.pop("current_user", None)
        self.manage_webinar = kwargs.pop("manage_webinar", False)
        self.is_personal = kwargs.pop("is_personal", False)
        super(MeetingForm, self).__init__(*args, **kwargs)

        self.set_queryset()
        self.filter_fields_admin()
        self.date_time_duration()
        self.filter_fields_webinar()
        # Manage required fields html
        self.fields = add_placeholder_and_asterisk(self.fields)

        if __FILEPICKER__ and self.fields.get("slides"):
            self.fields["slides"].widget = CustomFileWidget(type="file")
        if not self.initial.get("attendee_password"):
            self.initial["attendee_password"] = get_random_string(8)

        if getattr(self.instance, "id", None) and getattr(
            self.instance, "weekdays", None
        ):
            self.initial["days_of_week"] = list(self.instance.weekdays)
        # Remove recurring until value if recurrence is None
        if (
            getattr(self.instance, "id", None)
            and getattr(self.instance, "recurrence", None) is None
        ):
            self.initial["recurring_until"] = None
            self.initial["nb_occurrences"] = None

        self.filter_recording_fields()
        # remove start_at
        self.remove_field("start_at")
        # set min frequency to 1
        self.fields["frequency"].widget.attrs["min"] = 1
        # Manage personal meeting room
        self.manage_personal_meeting_room()

    def filter_recording_fields(self) -> None:
        """Hide recording options when the owner or editor may not record."""
        owner = getattr(self.instance, "owner", None) or self.current_user
        if not (
            meeting_recording_disabled(owner)
            or meeting_recording_disabled(self.current_user)
        ):
            return

        fields = MEETING_RECORD_FIELDS
        if not self.is_admin:
            fields = (*fields, *MEETING_RECORD_OPTION_FIELDS)
            self.fieldsets = tuple(
                fieldset
                for fieldset in self.fieldsets
                if fieldset[1].get("id") != "recording_fields"
            )

        for field in fields:
            self.remove_field(field)

    def manage_personal_meeting_room(self):
        """Manage fields for a personal meeting room."""
        if self.instance.is_personal:
            # Name is a readonly field in such a case
            self.fields["name"].widget.attrs["readonly"] = True
            # Hide time settings
            hidden_fields = (
                "start",
                "start_time",
                "expected_duration",
                "is_personal",
            )
            for field in hidden_fields:
                self.hide_field(field)

    def hide_field(self, field):
        """Hide a field from the form."""
        if self.fields.get(field):
            self.fields[field].widget = forms.HiddenInput()

    def remove_field(self, field):
        """Remove a field from the form."""
        if self.fields.get(field):
            del self.fields[field]

    def set_queryset(self):
        # if self.current_user is not None:
        #    users_groups = self.current_user.owner.accessgroup_set.all()
        if self.fields.get("owner"):
            self.fields["owner"].queryset = self.fields["owner"].queryset.filter(
                owner__sites=Site.objects.get_current()
            )
        self.fields["restrict_access_to_groups"].queryset = self.fields[
            "restrict_access_to_groups"
        ].queryset.filter(sites=Site.objects.get_current())

    def date_time_duration(self):
        if self.initial.get("expected_duration"):
            self.initial["expected_duration"] = int(
                self.initial.get("expected_duration").seconds / 3600
            )
        if getattr(self.instance, "id", None) and getattr(
            self.instance, "start_at", None
        ):
            self.initial["start"] = self.instance.start_at.date()
            self.initial["start_time"] = timezone.localtime(self.instance.start_at).time()

    class Meta(object):
        model = Meeting
        fields = "__all__"
        widgets = {
            "owner": OwnerWidget,
            "additional_owners": AddOwnerWidget,
            "recurring_until": admin_widgets.AdminDateWidget,
        }


class MeetingDeleteForm(forms.Form):
    agree = forms.BooleanField(
        label=_("I agree"),
        help_text=_("Delete meeting cannot be undone"),
        widget=forms.CheckboxInput(),
    )

    def __init__(self, *args, **kwargs):
        super(MeetingDeleteForm, self).__init__(*args, **kwargs)
        self.fields = add_placeholder_and_asterisk(self.fields)


class MeetingPasswordForm(forms.Form):
    name = forms.CharField(label=_("Name"))
    password = forms.CharField(label=_("Password"), widget=forms.PasswordInput())

    def __init__(self, *args, **kwargs):
        self.current_user = kwargs.pop("current_user", None)
        self.remove_password = kwargs.pop("remove_password", None)
        super(MeetingPasswordForm, self).__init__(*args, **kwargs)
        self.fields = add_placeholder_and_asterisk(self.fields)
        if self.current_user:
            self.remove_field("name")
        if self.remove_password:
            self.remove_field("password")

    def remove_field(self, field):
        if self.fields.get(field):
            del self.fields[field]


class EmailsListField(CharField):
    widget = Textarea

    def clean(self, value):
        super(EmailsListField, self).clean(value)

        emails = re.compile(r"[^\w\.\-\+@_]+").split(value)

        if not emails:
            raise ValidationError(_("Enter at least one e-mail address."))

        for email in emails:
            if email != "":
                validate_email(email)
            else:
                emails.remove(email)

        return emails


class MeetingInviteForm(forms.Form):
    emails = EmailsListField(
        label=_("Emails"),
        help_text=_("You can fill one email adress per line"),
    )
    owner_copy = forms.BooleanField(
        label="",
        required=False,
        help_text=_("Send invite to owner and additional owners"),
    )

    def __init__(self, *args, **kwargs):
        super(MeetingInviteForm, self).__init__(*args, **kwargs)
        self.fields = add_placeholder_and_asterisk(self.fields)
        self.fields["owner_copy"].widget.attrs.update({"class": "me-1"})


class InternalRecordingForm(forms.ModelForm):
    """Internal recording form.

    Args:
        forms (ModelForm): model form
    """

    site = forms.ModelChoiceField(Site.objects.all(), required=False)
    is_admin = False
    is_superuser = False

    fieldsets = (
        (
            None,
            {
                "fields": (
                    "name",
                    "source_url",
                    "start_at",
                    "owner",
                    "site",
                )
            },
        ),
    )

    def filter_fields_admin(form) -> None:
        """List fields, depends on user right."""
        if form.is_superuser is False and form.is_admin is False:
            form.remove_field("owner")
            form.remove_field("site")

    def clean(self) -> None:
        """Clean method."""
        cleaned_data = super(InternalRecordingForm, self).clean()
        try:
            validator = URLValidator()
            validator(cleaned_data["source_url"])
        except ValidationError:
            self.add_error("source_url", _("Please enter a valid address"))

    def __init__(self, *args, **kwargs) -> None:
        """Initialize recording form."""
        self.is_staff = (
            kwargs.pop("is_staff") if "is_staff" in kwargs.keys() else self.is_staff
        )

        self.is_superuser = (
            kwargs.pop("is_superuser")
            if ("is_superuser" in kwargs.keys())
            else self.is_superuser
        )
        self.current_lang = kwargs.pop("current_lang", settings.LANGUAGE_CODE)
        self.current_user = kwargs.pop("current_user", None)

        super(InternalRecordingForm, self).__init__(*args, **kwargs)

        self.set_queryset()
        self.filter_fields_admin()
        self.fields = add_placeholder_and_asterisk(self.fields)

        # We don't change the user who uploaded the record
        hidden_fields = ("uploaded_to_pod_by",)
        for field in hidden_fields:
            if self.fields.get(field, None):
                self.fields[field].widget = forms.HiddenInput()

    def remove_field(self, field):
        """Remove a field from the form."""
        if self.fields.get(field):
            del self.fields[field]

    def set_queryset(self):
        """Filter on owner."""
        if self.fields.get("owner"):
            self.fields["owner"].queryset = self.fields["owner"].queryset.filter(
                owner__sites=Site.objects.get_current()
            )

    class Meta(object):
        """Metadata options.

        Args:
            object (class): internal class
        """

        model = InternalRecording
        fields = "__all__"
        widgets = {
            "owner": OwnerWidget,
            "additional_owners": AddOwnerWidget,
        }
