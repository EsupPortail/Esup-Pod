"""Forms for the Meeting module."""
import datetime
import random
import re
import string

from .models import Meeting, InternalRecording
from django import forms
from django.conf import settings
from django.contrib.admin import widgets as admin_widgets
from django.contrib.sites.models import Site
from django.core.validators import validate_email, URLValidator
from django.core.exceptions import ValidationError
from django.db.models.query import QuerySet
from django.forms import CharField, Textarea
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _
from pod.main.forms_utils import add_placeholder_and_asterisk
from pod.main.forms_utils import OwnerWidget, AddOwnerWidget

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
MEETING_DATE_FIELDS = getattr(
    settings,
    "MEETING_DATE_FIELDS",
    (
        "start",
        "start_time",
        "expected_duration",
    ),
)
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
MEETING_DISABLE_RECORD = getattr(settings, "MEETING_DISABLE_RECORD", True)

MEETING_RECORD_FIELDS = getattr(
    settings,
    "MEETING_RECORD_FIELDS",
    ("record", "auto_start_recording"),  # , "allow_start_stop_recording"
)

__MEETING_EXCLUDE_FIELDS__ = (
    MEETING_MAIN_FIELDS
    + MEETING_DATE_FIELDS
    + MEETING_RECURRING_FIELDS
    + ("id", "start_at")
    + MEETING_RECORD_FIELDS
)


for field in Meeting._meta.fields:
    # print(field.name, field.editable)
    if field.editable is False:
        __MEETING_EXCLUDE_FIELDS__ = __MEETING_EXCLUDE_FIELDS__ + (field.name,)


def get_meeting_fields():
    fields = []
    for field in Meeting._meta.fields:
        if field.name not in __MEETING_EXCLUDE_FIELDS__:
            fields.append(field.name)
    return fields


def get_random_string(length):
    # choose from all lowercase letter
    letters = string.ascii_lowercase
    result_str = "".join(random.choice(letters) for i in range(length))
    return result_str


class MeetingForm(forms.ModelForm):
    site = forms.ModelChoiceField(Site.objects.all(), required=False)
    required_css_class = "required"
    is_admin = False
    is_superuser = False

    def get_time_choices(
        start_time=datetime.time(0, 0, 0),
        end_time=datetime.time(23, 0, 0),
        delta=datetime.timedelta(minutes=30),
    ):
        """
        Builds a choices tuple of (time object, time string) tuples
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
        label=_("Start date"), initial=timezone.now, widget=admin_widgets.AdminDateWidget
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
                "legend": ('<i class="bi bi-gear" aria-hidden="true"></i> %s' % _("Main fields")),
                "fields": MEETING_MAIN_FIELDS,
            },
        ),
        (
            "input-group",
            {
                "legend": (
                    '<i class="bi bi-clock-history" aria-hidden="true"></i>'
                    + " %s" % _("Date and time options")
                ),
                "fields": ["start", "start_time", "expected_duration"],
                "additional_data": """
                <div class="m-1">
                <button type="button" id="%s" class="%s" data-bs-toggle="%s" data-bs-target="%s">
                    <i class="bi bi-calendar3-range" aria-hidden="true"></i> %s
                </button>
                </div>
            """
                % (
                    "see_recurring_fields",
                    "btn btn-primary btn-sm",
                    "modal",
                    "#recurring_fields",
                    _("Recurring"),
                ),
            },
        ),
    )
    if not MEETING_DISABLE_RECORD:
        fieldsets += (
            (
                "input-group",
                {
                    "legend": (
                        '<i class="bi bi-record-circle" aria-hidden="true"></i>'
                        + " %s" % _("Record session")
                    ),
                    "fields": MEETING_RECORD_FIELDS,
                },
            ),
        )

    fieldsets += (
        (
            "modal",
            {
                "legend": (
                    '<i class="bi bi-calendar3-range" aria-hidden="true"></i>&nbsp;'
                    + "  %s" % _("Recurring options")
                ),
                "id": "recurring_fields",
                "fields": MEETING_RECURRING_FIELDS,
                "template": "meeting/recurring_options_modal_form.html",
            },
        ),
        (
            "advanced_options",
            {
                "legend": (
                    '<i class="bi bi-file-earmark-plus-fill" aria-hidden="true"></i>'
                    + " %s" % _("Advanced options")
                ),
                "classes": "collapse border border-primary p-1 m-1",
                "fields": get_meeting_fields(),
            },
        ),
    )

    def filter_fields_admin(form):
        if form.is_superuser is False and form.is_admin is False:
            form.remove_field("owner")

        if not hasattr(form, "admin_form"):
            form.remove_field("site")
        else:
            form.remove_field("days_of_week")

    def clean_start_date(self):
        """Check two things:
        - the start date is before the recurrence deadline.
        - in the case of weekly recurrence, the start day must be selected from the list of weekdays.
        The function raise a validation error if a condition is not met."""
        if ("start" in self.cleaned_data.keys()
            and "recurring_until" in self.cleaned_data.keys()
            and self.cleaned_data["recurring_until"] is not None
            and (
                self.cleaned_data["start"] > self.cleaned_data["recurring_until"]
        )):
            raise ValidationError(_("Start date must be less than recurring until date"))

        if (self.cleaned_data.get("weekdays")
            and self.cleaned_data.get("start")
            and self.cleaned_data.get("recurrence") == "weekly"
            and (
                str(self.cleaned_data.get("start").weekday())
                not in self.cleaned_data.get("weekdays")
        )):
            raise ValidationError(
                _("In case of weekly recurring, the day of the start date must be selected.")
            )

        if not self.cleaned_data.get('recurring_until'):
            self.instance.recurring_until = None

    def clean_add_owner(self):
        """Check if meeting owner not in additional owners."""
        if "additional_owners" in self.cleaned_data.keys() and isinstance(
            self.cleaned_data["additional_owners"], QuerySet
        ):
            meetingowner = (
                self.instance.owner
                if hasattr(self.instance, "owner")
                else self.cleaned_data["owner"]
                if "owner" in self.cleaned_data.keys()
                else self.current_user
            )
            if (
                meetingowner
                and meetingowner in self.cleaned_data["additional_owners"].all()
            ):
                raise ValidationError(
                    _("Owner of the video cannot be an additional owner too")
                )

    def clean(self):
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

        if "start_time" in self.cleaned_data.keys() and "start" in self.cleaned_data.keys():
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

    def __init__(self, *args, **kwargs):
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
        super(MeetingForm, self).__init__(*args, **kwargs)
        self.set_queryset()
        self.filter_fields_admin()
        self.date_time_duration()
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
        # remove recurring until value if recurrence is None
        if (
            getattr(self.instance, "id", None)
            and getattr(self.instance, "recurrence", None) is None
        ):
            self.initial["recurring_until"] = None

        # MEETING_DISABLE_RECORD
        if MEETING_DISABLE_RECORD:
            for field in MEETING_RECORD_FIELDS:
                self.remove_field(field)
        # remove start_at
        self.remove_field("start_at")
        # set min frequency to 1
        self.fields["frequency"].widget.attrs["min"] = 1

    def remove_field(self, field):
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

    def filter_fields_admin(form):
        """List fields, depends on user right."""
        if form.is_superuser is False and form.is_admin is False:
            form.remove_field("owner")
            form.remove_field("site")

    def clean(self):
        """Clean method."""
        cleaned_data = super(InternalRecordingForm, self).clean()
        try:
            validator = URLValidator()
            validator(cleaned_data["source_url"])
        except ValidationError:
            self.add_error("source_url", _("Please enter a valid address"))

    def __init__(self, *args, **kwargs):
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
