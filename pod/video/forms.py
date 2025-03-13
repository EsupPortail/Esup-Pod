"""Forms for Esup-Pod video app."""

from django import forms
from django.contrib.admin import widgets
from django.contrib.auth.models import User
from django.conf import settings
from django.core.validators import FileExtensionValidator
from django.core.exceptions import ValidationError
from django.forms.widgets import ClearableFileInput
from django.utils.deconstruct import deconstructible
from django.utils.translation import gettext_lazy as _
from django.template.defaultfilters import filesizeformat
from .models import Video, VideoVersion, get_storage_path_video
from .models import Channel
from .models import Theme
from .models import Type
from .models import Discipline
from .models import Notes, AdvancedNotes, NoteComments
from pod.video_encode_transcript.models import PlaylistVideo
from pod.video_encode_transcript import encode
from pod.video_encode_transcript.models import EncodingVideo, EncodingAudio
from django.contrib.sites.models import Site
from django.db.models.query import QuerySet

from django.dispatch import receiver
from django.db.models.signals import post_save
from django.contrib.sites.shortcuts import get_current_site
from pod.main.forms_utils import add_placeholder_and_asterisk, add_describedby_attr

from tinymce.widgets import TinyMCE
from collections import OrderedDict
from django_select2 import forms as s2forms

import datetime
from dateutil.relativedelta import relativedelta
import os
import re

__FILEPICKER__ = False
if getattr(settings, "USE_PODFILE", False):
    __FILEPICKER__ = True
    from pod.podfile.widgets import CustomFileWidget

MAX_DURATION_DATE_DELETE = getattr(settings, "MAX_DURATION_DATE_DELETE", 10)

# __TODAY__ = datetime.date.today()

# __MAX_D__ = __TODAY__ + datetime.timedelta(days=MAX_DURATION_DATE_DELETE * 365)

USE_TRANSCRIPTION = getattr(settings, "USE_TRANSCRIPTION", False)

ENCODE_VIDEO = getattr(settings, "ENCODE_VIDEO", "start_encode")

USE_OBSOLESCENCE = getattr(settings, "USE_OBSOLESCENCE", False)

ACTIVE_VIDEO_COMMENT = getattr(settings, "ACTIVE_VIDEO_COMMENT", False)

VIDEO_REQUIRED_FIELDS = getattr(settings, "VIDEO_REQUIRED_FIELDS", [])

VIDEO_ALLOWED_EXTENSIONS = getattr(
    settings,
    "VIDEO_ALLOWED_EXTENSIONS",
    (
        "3gp",
        "avi",
        "divx",
        "flv",
        "m2p",
        "m4v",
        "mkv",
        "mov",
        "mp4",
        "mpeg",
        "mpg",
        "mts",
        "wmv",
        "mp3",
        "ogg",
        "wav",
        "wma",
        "webm",
        "ts",
    ),
)
VIDEO_MAX_UPLOAD_SIZE = getattr(settings, "VIDEO_MAX_UPLOAD_SIZE", 1)

VIDEO_FORM_FIELDS_HELP_TEXT = getattr(
    settings,
    "VIDEO_FORM_FIELDS_HELP_TEXT",
    OrderedDict(
        [
            (
                "{0}".format(_("File field")),
                [
                    _("You can send an audio or video file."),
                    _("The following formats are supported: %s")
                    % ", ".join(map(str, VIDEO_ALLOWED_EXTENSIONS)),
                ],
            ),
            (
                "{0}".format(_("Title field")),
                [
                    _(
                        "Please choose a title as short and accurate as possible, "
                        "reflecting the main subject / context of the content."
                    ),
                    _(
                        "You can use the “Description” field below for all "
                        "additional information."
                    ),
                    _(
                        "You may add contributors later using the second button of "
                        "the content edition toolbar: they will appear in the “Info” "
                        "tab at the bottom of the audio / video player."
                    ),
                ],
            ),
            (
                "{0}".format(_("Type")),
                [
                    _(
                        "Select the type of your content. If the type you wish does "
                        "not appear in the list, please temporary select “Other” "
                        "and contact us to explain your needs."
                    )
                ],
            ),
            (
                "{0}".format(_("Additional owners")),
                [
                    _(
                        "In this field you can select and add additional owners to the "
                        "video. These additional owners will have the same rights as "
                        "you except that they can’t delete this media."
                    )
                ],
            ),
            (
                "{0}".format(_("Description")),
                [
                    _(
                        "In this field you can describe your content, add all needed "
                        "related information, and format the result "
                        "using the toolbar."
                    )
                ],
            ),
            (
                "{0}".format(_("Date of the event field")),
                [
                    _(
                        "Enter the date of the event, if applicable, in the "
                        "AAAA-MM-JJ format."
                    )
                ],
            ),
            (
                "{0}".format(_("University course")),
                [
                    _(
                        "Select an university course as audience target of "
                        "the content."
                    ),
                    _(
                        "Choose “None / All” if it does not apply or if all are "
                        "concerned, or “Other” for an audience outside "
                        "the european LMD scheme."
                    ),
                ],
            ),
            (
                "{0}".format(_("Main language")),
                [_("Select the main language used in the content.")],
            ),
            (
                "{0}".format(_("Tags")),
                [
                    _(
                        "Please try to add only relevant keywords that can be "
                        "useful to other users."
                    )
                ],
            ),
            (
                "{0}".format(_("Disciplines")),
                [
                    _(
                        "Select the discipline to which your content belongs. "
                        "If the discipline you wish does not appear in the list, "
                        "please select nothing and contact us to explain your needs."
                    ),
                    _(
                        'Hold down "Control", or "Command" on a Mac, '
                        "to select more than one."
                    ),
                ],
            ),
            (
                "{0}".format(_("Licence")),
                [
                    (
                        '<a href="https://creativecommons.org/licenses/by/4.0/"'
                        ' target="_blank">%(lic)s</a>'
                    )
                    % {"lic": _("Attribution 4.0 International (CC BY 4.0)")},
                    (
                        '<a href="https://creativecommons.org/licenses/by-nd/4.0/"'
                        ' target="_blank">%(lic)s</a>'
                    )
                    % {
                        "lic": _(
                            "Attribution-NoDerivatives 4.0 "
                            "International (CC BY-ND 4.0)"
                        )
                    },
                    (
                        '<a href="https://creativecommons.org/licenses/by-nc-nd/4.0/"'
                        ' target="_blank">%(lic)s</a>'
                    )
                    % {
                        "lic": _(
                            "Attribution-NonCommercial-NoDerivatives 4.0 "
                            "International (CC BY-NC-ND 4.0)"
                        )
                    },
                    (
                        '<a href="https://creativecommons.org/licenses/by-nc/4.0/"'
                        ' target="_blank">%(lic)s</a>'
                    )
                    % {
                        "lic": _(
                            "Attribution-NonCommercial 4.0 "
                            "International (CC BY-NC 4.0)"
                        )
                    },
                    (
                        '<a href="https://creativecommons.org/licenses/by-nc-sa/4.0/"'
                        ' target="_blank">%(lic)s</a>'
                    )
                    % {
                        "lic": _(
                            "Attribution-NonCommercial-ShareAlike 4.0 "
                            "International (CC BY-NC-SA 4.0)"
                        )
                    },
                    (
                        '<a href="https://creativecommons.org/licenses/by-sa/4.0/"'
                        ' target="_blank">%(lic)s</a>'
                    )
                    % {
                        "lic": _(
                            "Attribution-ShareAlike 4.0 International (CC BY-SA 4.0)"
                        )
                    },
                ],
            ),
            (
                "{0} / {1}".format(_("Channels"), _("Themes")),
                [
                    _("Select the channel in which you want your content to appear."),
                    _(
                        "Themes related to this channel will "
                        "appear in the “Themes” list below."
                    ),
                    _(
                        'Hold down "Control", or "Command" on a Mac, '
                        "to select more than one."
                    ),
                    _(
                        "If the channel or theme you wish does not appear "
                        "in the list, please select nothing and contact "
                        "us to explain your needs."
                    ),
                ],
            ),
            (
                "{0}".format(_("Visibility")),
                [
                    _("In “Public” mode, the content is visible to everyone."),
                    _(
                        "In “Draft / Private” mode, the content shows nowhere and nobody "
                        "else but you can see it."
                    ),
                    _(
                        "In “Restricted access” mode, you can choose the restrictions for the video."
                    ),
                ],
            ),
            (
                "{0}".format(_("Password")),
                [
                    _(
                        "In “Restricted access” mode, you can add a password "
                        "which will be asked to anybody willing to watch "
                        "your content. You can add tokens for allow direct access by link."
                    ),
                    _(
                        "If your video is in a playlist the password of your "
                        "video will be removed automatically."
                    ),
                ],
            ),
            (
                "{0}".format(_("Authentication restricted access")),
                [
                    _(
                        "In “Restricted access” mode, you can restrict "
                        "the content access to only people who can log in"
                    )
                ],
            ),
            (
                "{0}".format(_("Groups")),
                [
                    _(
                        "In “Restricted access” mode, you can restrict "
                        "the content access to only people who are in these groups."
                    )
                ],
            ),
        ]
    ),
)

if USE_TRANSCRIPTION:
    from ..video_encode_transcript import transcript

    TRANSCRIPT_VIDEO = getattr(settings, "TRANSCRIPT_VIDEO", "start_transcript")

    transcript_help_text = OrderedDict(
        [
            (
                "{0}".format(_("Transcript")),
                [
                    _(
                        "Transcription is a speech"
                        " recognition technology that transforms an oral speech into "
                        "text in an automated way. By selecting language, it will "
                        "generate a subtitle file automatically when encoding the video."
                    ),
                    _(
                        "You will probably have to modify this file using the "
                        "captioning tool in the completion page to improve it."
                    ),
                ],
            )
        ]
    )
    VIDEO_FORM_FIELDS_HELP_TEXT.update(transcript_help_text)

VIDEO_FORM_FIELDS = getattr(settings, "VIDEO_FORM_FIELDS", "__all__")


CHANNEL_FORM_FIELDS_HELP_TEXT = getattr(
    settings,
    "CHANNEL_FORM_FIELDS_HELP_TEXT",
    OrderedDict(
        [
            (
                "{0}".format(_("Title field")),
                [
                    _(
                        "Please choose a title as short and accurate as possible, "
                        "reflecting the main subject / context of the content."
                    ),
                    _(
                        "You can use the “Description” field below for all "
                        "additional information."
                    ),
                ],
            ),
            (
                "{0}".format(_("Description")),
                [
                    _(
                        "In this field you can describe your content, add all needed "
                        "related information, and format the result "
                        "using the toolbar."
                    )
                ],
            ),
            (
                ("{0} / {1}".format(_("Extra style"), _("Background color"))),
                [
                    _(
                        "In this field you can add some style to personnalize "
                        "your channel."
                    )
                ],
            ),
            (
                ("{0} / {1}".format(_("Owners"), _("Users"))),
                [
                    _(
                        "Owners can add videos to this channel "
                        "and access this page to customize the channel."
                    ),
                    _("Users can only add videos to this channel"),
                ],
            ),
        ]
    ),
)

THEME_FORM_FIELDS_HELP_TEXT = getattr(
    settings,
    "THEME_FORM_FIELDS_HELP_TEXT",
    OrderedDict(
        [
            (
                "{0}".format(_("Title field")),
                [
                    _(
                        "Please choose a title as short and accurate as possible, "
                        "reflecting the main subject / context of the content."
                    ),
                    _(
                        "You can use the “Description” field below for all "
                        "additional information."
                    ),
                ],
            ),
            (
                "{0}".format(_("Description")),
                [
                    _(
                        "In this field you can describe your content, add all needed "
                        "related information, and format the result "
                        "using the toolbar."
                    )
                ],
            ),
        ]
    ),
)


class CustomClearableFileInput(ClearableFileInput):
    """A custom ClearableFileInput Widget a little more accessible."""

    template_name = "videos/widgets/customclearablefileinput.html"


class OwnerWidget(s2forms.ModelSelect2Widget):
    """Widget for selecting a single owner."""

    search_fields = [
        "username__icontains",
        "email__icontains",
    ]


class AddOwnerWidget(s2forms.ModelSelect2MultipleWidget):
    """Widget for selecting multiple owners."""

    search_fields = [
        "username__icontains",
        "email__icontains",
    ]


class AddAccessGroupWidget(s2forms.ModelSelect2MultipleWidget):
    """Widget for selecting multiple access groups."""

    search_fields = [
        "display_name__icontains",
        "code_name__icontains",
    ]


class ChannelWidget(s2forms.ModelSelect2MultipleWidget):
    """Widget for selecting multiple channels."""

    search_fields = [
        "title__icontains",
    ]


class DisciplineWidget(s2forms.ModelSelect2MultipleWidget):
    """Widget for selecting multiple disciplines."""

    search_fields = [
        "title__icontains",
    ]


class SelectWOA(forms.widgets.Select):
    """
    Select With Option Attributes.

        subclass of Django's Select widget that allows attributes in options,
        like disabled="disabled", title="help text", class="some classes",
              style="background: color;"...

    Pass a dict instead of a string for its label:
        choices = [ ('value_1', 'label_1'),
                    ...
                    ('value_k', {'label': 'label_k', 'foo': 'bar', ...}),
                    ... ]
    The option k will be rendered as:
        <option value="value_k" foo="bar" ...>label_k</option>
    """

    def create_option(
        self, name, value, label, selected, index, subindex=None, attrs=None
    ):
        """Replace the option creators from original Select."""
        # This allows using strings labels as usual
        if isinstance(label, dict):
            opt_attrs = label.copy()
            label = opt_attrs.pop("label")
        else:
            opt_attrs = {}
        option_dict = super(SelectWOA, self).create_option(
            name, value, label, selected, index, subindex=subindex, attrs=attrs
        )
        for key, val in opt_attrs.items():
            option_dict["attrs"][key] = val
        return option_dict


class DescribedChoiceField(forms.ModelChoiceField):
    """ChoiceField with description on <options> titles."""

    # Use custom widget "Select With Option Attribute"
    widget = SelectWOA

    def label_from_instance(self, obj):
        """Override parent's label_from_instance method."""
        return {
            # the usual label:
            "label": super().label_from_instance(obj),
            # the new title attribute:
            "title": obj.description,
        }


@deconstructible
class FileSizeValidator(object):
    """File size validator."""

    message = _(
        "The current file %(size)s, which is too large. "
        "The maximum file size is %(allowed_size)s."
    )
    code = "invalid_max_size"

    def __init__(self, *args, **kwargs):
        """Initialize a new FileSizeValidator instance."""
        self.max_size = VIDEO_MAX_UPLOAD_SIZE * 1024 * 1024 * 1024  # GO

    def __call__(self, value):
        # Check the file size
        filesize = len(value)
        if self.max_size and filesize > self.max_size:
            raise ValidationError(
                self.message,
                code=self.code,
                params={
                    "size": filesizeformat(filesize),
                    "allowed_size": filesizeformat(self.max_size),
                },
            )


@receiver(post_save, sender=Video)
def launch_encode(sender, instance, created, **kwargs) -> None:
    """
    Launch encoding after save Video if requested.

    Args:
        sender (:class:`pod.video.models.Video`): Video model class.
        instance (:class:`pod.video.models.Video`): Video object instance.
    """
    if hasattr(instance, "launch_encode") and instance.launch_encode is True:
        instance.launch_encode = False
        encode_video = getattr(encode, ENCODE_VIDEO)
        encode_video(instance.id)


@receiver(post_save, sender=Video)
def launch_transcript(sender, instance, created, **kwargs) -> None:
    """
    Launch transcription after save Video if requested.

    Args:
        sender (:class:`pod.video.models.Video`): Video model class.
        instance (:class:`pod.video.models.Video`): Video object instance.
    """
    if hasattr(instance, "launch_transcript") and instance.launch_transcript is True:
        instance.launch_transcript = False
        transcript_video = getattr(transcript, TRANSCRIPT_VIDEO)
        transcript_video(instance.id)


class VideoForm(forms.ModelForm):
    """Form class for Video editing."""

    VISIBILITY_CHOICES = [
        ("public", _("Public")),
        ("draft", _("Draft / Private")),
        ("restricted", _("Restricted access")),
    ]

    visibility = forms.ChoiceField(
        choices=VISIBILITY_CHOICES,
        label=_("Visibility"),
        required=True,
        initial="public",
        help_text=_("Who can see your content (everyone, just you, or those granted)."),
    )

    required_css_class = "required"
    videoattrs = {
        "class": "form-control-file",
        "accept": "audio/*, video/*, .%s"
        % ", .".join(map(str, VIDEO_ALLOWED_EXTENSIONS)),
    }
    is_admin = False
    user = User.objects.all()

    fieldsets = (
        (
            "file",
            {
                "legend": _("Source file"),
                "classes": "show",
                "fields": [
                    "video",
                ],
            },
        ),
        (
            "general",
            {
                "legend": _("General settings"),
                "classes": "show",
                "fields": [
                    "title",
                    "title_en",
                    "sites",
                    "type",
                    "owner",
                    "additional_owners",
                    "description",
                    "description_en",
                    "date_added",
                    "date_evt",
                    "cursus",
                    "main_lang",
                    "transcript",
                    "tags",
                    "discipline",
                    "licence",
                    "thumbnail",
                    "date_delete",
                ],
            },
        ),
        (
            "channel_option",
            {
                "legend": _("Channel options"),
                "classes": "show",
                "fields": [
                    "channel",
                    "theme",
                ],
            },
        ),
        (
            "access_restrictions",
            {
                "legend": _("Restrictions"),
                "classes": "show",
                "fields": [
                    "visibility",
                    "is_draft",
                    "is_restricted",
                    "restrict_access_to_groups",
                    "password",
                ],
            },
        ),
        (
            "advanced_options",
            {
                "legend": _("Advanced options"),
                "classes": "",
                "fields": ["allow_downloading", "is_360", "disable_comment", "order"],
            },
        ),
    )

    def filter_fields_admin(form) -> None:
        """Hide fields reserved for admins."""
        if form.is_superuser is False and form.is_admin is False:
            form.remove_field("date_added")
            form.remove_field("owner")

        if not hasattr(form, "admin_form"):
            form.remove_field("sites")

    def create_with_fields(self, field_key) -> None:
        """Create VideoForm with specific fields. Keep video field to prevent error on save."""
        fields = set(self.fields)
        if "description" in field_key:
            field_key.append("description_%s" % self.current_lang)
        if "title" in field_key:
            field_key.append("title_%s" % self.current_lang)
        for field in fields:
            if field not in field_key and field != "video":
                del self.fields[field]

    def move_video_source_file(self, new_path, new_dir, old_dir) -> None:
        """Move video source file in a new dir."""
        # create user repository
        dest_file = os.path.join(settings.MEDIA_ROOT, new_path)
        os.makedirs(os.path.dirname(dest_file), exist_ok=True)
        # move video
        os.rename(
            os.path.join(settings.MEDIA_ROOT, self.cleaned_data["video"].name),
            dest_file,
        )
        # change path for video
        self.instance.video = new_path
        # Move Dir
        os.rename(
            os.path.join(settings.MEDIA_ROOT, old_dir),
            os.path.join(settings.MEDIA_ROOT, new_dir),
        )
        # Overview
        if self.instance.overview:
            self.instance.overview = self.instance.overview.name.replace(old_dir, new_dir)

    def change_encoded_path(self, video, new_dir, old_dir) -> None:
        """Change the path of encodings related to a video."""
        models_to_update = [EncodingVideo, EncodingAudio, PlaylistVideo]
        for model in models_to_update:
            encodings = model.objects.filter(video=video)
            for encoding in encodings:
                encoding.source_file = encoding.source_file.name.replace(old_dir, new_dir)
                encoding.save()

    def save_visibility(self) -> None:
        """Save video access fields depends on the visibility field value."""
        visibility = self.cleaned_data.get("visibility")
        if visibility == "public":
            self.instance.is_draft = False
            self.instance.is_restricted = False
            self.instance.password = None
        elif visibility == "draft":
            self.instance.is_draft = True
            self.instance.is_restricted = False
            self.instance.password = None
        elif visibility == "restricted":
            self.instance.is_draft = False

    def save(self, commit=True, *args, **kwargs):
        """Save video and launch encoding if relevant."""
        self.save_visibility()
        old_dir = ""
        new_dir = ""
        if hasattr(self, "change_user") and self.change_user is True:
            # create new video file
            storage_path = get_storage_path_video(
                self.instance, os.path.basename(self.cleaned_data["video"].name)
            )
            dt = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            nom, ext = os.path.splitext(os.path.basename(self.cleaned_data["video"].name))
            ext = ext.lower()
            nom = re.sub(r"_\d{4}-\d{2}-\d{2}_\d{2}-\d{2}-\d{2}$", "", nom)
            new_path = os.path.join(os.path.dirname(storage_path), nom + "_" + dt + ext)
            if self.instance.overview:
                old_dir = os.path.dirname(self.instance.overview.name)
            else:
                old_dir = os.path.join(
                    os.path.dirname(self.cleaned_data["video"].name),
                    "%04d" % self.instance.id,
                )
            new_dir = os.path.join(os.path.dirname(new_path), "%04d" % self.instance.id)
            self.move_video_source_file(new_path, new_dir, old_dir)

        video = super(VideoForm, self).save(commit, *args, **kwargs)

        if hasattr(self, "change_user") and self.change_user is True:
            self.change_encoded_path(video, new_dir, old_dir)

        if hasattr(self, "launch_encode"):
            video.launch_encode = self.launch_encode

        if hasattr(self, "launch_transcript"):
            video.launch_transcript = self.launch_transcript
        return video

    def clean_date_delete(self):
        """Validate 'date_delete' field."""
        today_date = datetime.date.today()
        mddd = MAX_DURATION_DATE_DELETE
        date_delete = self.cleaned_data["date_delete"]
        in_dt = relativedelta(date_delete, today_date)
        if (
            (in_dt.years > mddd)
            or (in_dt.years == mddd and in_dt.months > 0)
            or (in_dt.years == mddd and in_dt.months == 0 and in_dt.days > 0)
        ):
            max_d = today_date + datetime.timedelta(days=MAX_DURATION_DATE_DELETE * 365)
            raise ValidationError(
                _(
                    "The date must be before or equal to %(date)s."
                    % {"date": max_d.strftime("%d-%m-%Y")}
                ),
                code="date_too_far",
            )
        if date_delete < today_date:
            raise ValidationError(
                _("The deletion date can’t be earlier than today."),
                code="date_before_today",
            )
        return self.cleaned_data["date_delete"]

    def check_visibility(self, cleaned_data) -> None:
        """Check the visibility field."""
        visibility = cleaned_data.get("visibility", "")
        is_restricted = cleaned_data.get("is_restricted", False)
        password = cleaned_data.get("password", "")
        if visibility == "restricted" and is_restricted is False and password is None:
            raise ValidationError(
                _(
                    'If you select restricted visibility for your video, you must check the "restricted access" box or specify a password.'
                )
            )

    def clean(self) -> None:
        """Validate Video form fields."""
        cleaned_data = super(VideoForm, self).clean()
        self.check_visibility(cleaned_data)
        if "additional_owners" in cleaned_data.keys() and isinstance(
            self.cleaned_data["additional_owners"], QuerySet
        ):
            vidowner = (
                self.instance.owner
                if hasattr(self.instance, "owner")
                else (
                    cleaned_data["owner"]
                    if "owner" in cleaned_data.keys()
                    else self.current_user
                )
            )
            if vidowner and vidowner in self.cleaned_data["additional_owners"].all():
                raise ValidationError(
                    _("Owner of the video cannot be an additional owner too")
                )

        self.launch_encode = (
            "video" in cleaned_data.keys()
            and hasattr(self.instance, "video")
            and cleaned_data["video"] != self.instance.video
        )
        # self.launch_transcript = "transcript" in cleaned_data.keys() and hasattr(
        #     self.instance, "transcript"
        # )
        self.change_user = (
            self.launch_encode is False
            and hasattr(self.instance, "encoding_in_progress")
            and self.instance.encoding_in_progress is False
            and hasattr(self.instance, "owner")
            and "owner" in cleaned_data.keys()
            and cleaned_data["owner"] != self.instance.owner
        )
        if "description" in cleaned_data.keys():
            cleaned_data["description_%s" % self.current_lang] = cleaned_data[
                "description"
            ]
        if "title" in cleaned_data.keys():
            cleaned_data["title_%s" % self.current_lang] = cleaned_data["title"]
        if (
            "restrict_access_to_groups" in cleaned_data.keys()
            and len(cleaned_data["restrict_access_to_groups"]) > 0
        ):
            cleaned_data["is_restricted"] = True

    def clean_channel(self):
        """Merge channels of a video."""
        if self.current_user is not None:
            users_groups = self.current_user.owner.accessgroup_set.all()
            if self.is_superuser:
                user_channels = Channel.objects.all()
            else:
                user_channels = (
                    self.current_user.owners_channels.all()
                    | self.current_user.users_channels.all()
                    | Channel.objects.filter(allow_to_groups__in=users_groups)
                ).distinct()

            user_channels.filter(site=get_current_site(None))
            channels_to_keep = Video.objects.get(pk=self.instance.id).channel.exclude(
                pk__in=[c.id for c in user_channels]
            )
            return self.cleaned_data["channel"].union(channels_to_keep)
        else:
            return self.cleaned_data["channel"]

    def __init__(self, *args, **kwargs) -> None:
        """Initialize a new VideoForm instance."""
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

        self.VIDEO_ALLOWED_EXTENSIONS = VIDEO_ALLOWED_EXTENSIONS
        self.VIDEO_MAX_UPLOAD_SIZE = VIDEO_MAX_UPLOAD_SIZE
        self.VIDEO_FORM_FIELDS_HELP_TEXT = VIDEO_FORM_FIELDS_HELP_TEXT
        self.max_duration_date_delete = MAX_DURATION_DATE_DELETE

        super(VideoForm, self).__init__(*args, **kwargs)

        self.custom_video_form()
        # change WYSIWYG, thumbnail and date delete config for non staff user
        self.set_nostaff_config()
        # hide default language
        self.hide_default_language()
        # QuerySet for channels and theme
        self.set_queryset()
        self.filter_fields_admin()
        # Manage more required fields
        self.manage_more_required_fields()
        # Manage required fields html
        self.fields = add_placeholder_and_asterisk(self.fields)
        self.fields = add_describedby_attr(self.fields)
        if self.fields.get("video"):
            # Remove label, as it will be included in customclearablefileinput
            self.fields["video"].label = ""
            valid_ext = FileExtensionValidator(VIDEO_ALLOWED_EXTENSIONS)
            self.fields["video"].validators = [valid_ext, FileSizeValidator]
            self.fields["video"].widget.attrs["class"] = self.videoattrs["class"]
            self.fields["video"].widget.attrs["accept"] = self.videoattrs["accept"]

        if self.instance and self.instance.video:
            if self.instance.encoding_in_progress or not self.instance.encoded:
                if not self.is_superuser:
                    self.remove_field("owner")
                self.remove_field("video")  # .widget = forms.HiddenInput()
                self.remove_field("thumbnail")

        # remove required=True for videofield if instance
        if self.fields.get("video") and self.instance and self.instance.video:
            # remove del self.fields["video"].widget.attrs["required"]
            self.fields["video"].widget.attrs.pop("required", None)
        if self.fields.get("owner"):
            self.fields["owner"].queryset = self.fields["owner"].queryset.filter(
                owner__sites=Site.objects.get_current()
            )
        self.__init_instance__()

    def __init_instance__(self) -> None:
        """Initialize a new VideoForm instance for visibility field."""
        if self.instance:
            if self.instance.is_draft:
                self.initial["visibility"] = "draft"
            elif self.instance.is_restricted or self.instance.password:
                self.initial["visibility"] = "restricted"
            else:
                self.initial["visibility"] = "public"
        self.fields["is_draft"].widget = forms.HiddenInput()
        self.order_fields(["visibility", "password"] + list(self.fields.keys()))

    def custom_video_form(self) -> None:
        if not ACTIVE_VIDEO_COMMENT:
            self.remove_field("disable_comment")

        if __FILEPICKER__ and self.fields.get("thumbnail"):
            self.fields["thumbnail"].widget = CustomFileWidget(type="image")

        if not USE_TRANSCRIPTION:
            self.remove_field("transcript")

    def manage_more_required_fields(self) -> None:
        """Set the required attribute to True for all VIDEO_REQUIRED_FIELDS."""
        for field in VIDEO_REQUIRED_FIELDS:
            # field exists, not hide
            if self.fields.get(field, None):
                self.fields[field].required = True

    def set_nostaff_config(self) -> None:
        """Set the configuration for non staff user."""
        if self.is_staff is False:
            del self.fields["thumbnail"]

            self.fields["description"].widget = TinyMCE()
            for key, _value in settings.LANGUAGES:
                self.fields["description_%s" % key.replace("-", "_")].widget = TinyMCE()
        if self.fields.get("date_delete"):
            if self.is_staff is False or USE_OBSOLESCENCE is False:
                del self.fields["date_delete"]
            else:
                self.fields["date_delete"].widget = forms.DateInput(
                    format=("%Y-%m-%d"),
                    attrs={"type": "date"},
                )

    def hide_default_language(self) -> None:
        """Hide default language."""
        if self.fields.get("description_%s" % settings.LANGUAGE_CODE):
            self.fields["description_%s" % settings.LANGUAGE_CODE].widget = (
                forms.HiddenInput()
            )
        if self.fields.get("title_%s" % settings.LANGUAGE_CODE):
            self.fields["title_%s" % settings.LANGUAGE_CODE].widget = forms.HiddenInput()

    def remove_field(self, field) -> None:
        """Remove a field from the form."""
        if self.fields.get(field):
            del self.fields[field]

    def set_queryset(self) -> None:
        """Set the queryset for the form fields."""
        if self.current_user is not None:
            users_groups = self.current_user.owner.accessgroup_set.all()
            user_channels = (
                Channel.objects.all()
                if self.is_superuser
                else (
                    self.current_user.owners_channels.all()
                    | self.current_user.users_channels.all()
                    | Channel.objects.filter(allow_to_groups__in=users_groups)
                ).distinct()
            )
            user_channels.filter(site=get_current_site(None))
            if user_channels:
                self.fields["channel"].queryset = user_channels
                list_theme = Theme.objects.filter(channel__in=user_channels).order_by(
                    "channel", "title"
                )
                self.fields["theme"].queryset = list_theme
            else:
                del self.fields["theme"]
                del self.fields["channel"]
        self.fields["type"].queryset = Type.objects.all().filter(
            sites=Site.objects.get_current()
        )
        self.fields["restrict_access_to_groups"].queryset = self.fields[
            "restrict_access_to_groups"
        ].queryset.filter(sites=Site.objects.get_current())
        self.fields["discipline"].queryset = Discipline.objects.all().filter(
            site=Site.objects.get_current()
        )
        if "channel" in self.fields:
            self.fields["channel"].queryset = self.fields["channel"].queryset.filter(
                site=Site.objects.get_current()
            )

        if "theme" in self.fields:
            self.fields["theme"].queryset = self.fields["theme"].queryset.filter(
                channel__site=Site.objects.get_current()
            )

    class Meta(object):
        """Define the VideoForm metadata."""

        model = Video
        fields = VIDEO_FORM_FIELDS
        field_classes = {"type": DescribedChoiceField}
        widgets = {
            "owner": OwnerWidget,
            "additional_owners": AddOwnerWidget,
            "channel": ChannelWidget(attrs={"data-minimum-input-length": 0}),
            "discipline": DisciplineWidget(attrs={"data-minimum-input-length": 0}),
            "date_evt": widgets.AdminDateWidget,
            "restrict_access_to_groups": AddAccessGroupWidget,
            "video": CustomClearableFileInput,
            "password": forms.TextInput(),
        }
        initial = {
            "date_added": datetime.date.today(),
            "date_evt": datetime.date.today(),
        }


class ChannelForm(forms.ModelForm):
    """Form class for Channel editing."""

    site = forms.ModelChoiceField(Site.objects.all(), required=False)

    fieldsets = (
        (
            "general",
            {
                "legend": _("General settings"),
                "classes": "show",
                "fields": [
                    "title",
                    "description",
                    "color",
                    "style",
                    "owners",
                    "users",
                    "visible",
                    "allow_to_groups",
                    "add_channels_tab",
                ],
            },
        ),
        (
            "headband",
            {
                "legend": _("Headband"),
                "classes": "show",
                "fields": [
                    "headband",
                ],
            },
        ),
    )

    def clean(self) -> None:
        cleaned_data = super(ChannelForm, self).clean()
        if "description" in cleaned_data.keys():
            cleaned_data["description_%s" % settings.LANGUAGE_CODE] = cleaned_data[
                "description"
            ]
        if "title" in cleaned_data.keys():
            cleaned_data["title_%s" % settings.LANGUAGE_CODE] = cleaned_data["title"]

    def __init__(self, *args, **kwargs) -> None:
        """Initialize a new ChannelForm instance."""
        self.is_staff = (
            kwargs.pop("is_staff") if "is_staff" in kwargs.keys() else self.is_staff
        )
        self.is_superuser = (
            kwargs.pop("is_superuser")
            if ("is_superuser" in kwargs.keys())
            else self.is_superuser
        )

        self.CHANNEL_FORM_FIELDS_HELP_TEXT = CHANNEL_FORM_FIELDS_HELP_TEXT

        super(ChannelForm, self).__init__(*args, **kwargs)
        if __FILEPICKER__:
            self.fields["headband"].widget = CustomFileWidget(type="image")

        if not hasattr(self, "admin_form"):
            del self.fields["visible"]
            if self.fields.get("site"):
                del self.fields["site"]
        if not self.is_superuser or not hasattr(self, "admin_form"):
            self.fields["owners"].queryset = self.fields["owners"].queryset.filter(
                owner__sites=Site.objects.get_current()
            )
            self.fields["users"].queryset = self.fields["users"].queryset.filter(
                owner__sites=Site.objects.get_current()
            )

        # change WYSIWYG config for no staff user
        if not hasattr(self, "admin_form") and (
            self.is_staff is False and self.is_superuser is False
        ):
            del self.fields["headband"]
            self.fields["description"].widget = TinyMCE()
            for key, _value in settings.LANGUAGES:
                self.fields["description_%s" % key.replace("-", "_")].widget = TinyMCE()
        # hide default langage
        self.fields["description_%s" % settings.LANGUAGE_CODE].widget = (
            forms.HiddenInput()
        )
        self.fields["title_%s" % settings.LANGUAGE_CODE].widget = forms.HiddenInput()

        self.fields = add_placeholder_and_asterisk(self.fields)
        self.fields = add_describedby_attr(self.fields)

    class Meta(object):
        """Define the ChannelForm metadata."""

        model = Channel
        fields = "__all__"
        widgets = {
            "owners": AddOwnerWidget,
            "users": AddOwnerWidget,
            "allow_to_groups": AddAccessGroupWidget,
        }


class ThemeForm(forms.ModelForm):
    """Form class for Theme editing."""

    def __init__(self, *args, **kwargs) -> None:
        """Initialize a new ThemeForm instance."""
        super(ThemeForm, self).__init__(*args, **kwargs)
        if __FILEPICKER__:
            self.fields["headband"].widget = CustomFileWidget(type="image")

        # hide default langage
        self.fields["description_%s" % settings.LANGUAGE_CODE].widget = (
            forms.HiddenInput()
        )
        self.fields["title_%s" % settings.LANGUAGE_CODE].widget = forms.HiddenInput()

        self.fields = add_placeholder_and_asterisk(self.fields)

    def clean(self) -> None:
        cleaned_data = super(ThemeForm, self).clean()
        if "description" in cleaned_data.keys():
            cleaned_data["description_%s" % settings.LANGUAGE_CODE] = cleaned_data[
                "description"
            ]
        if "title" in cleaned_data.keys():
            cleaned_data["title_%s" % settings.LANGUAGE_CODE] = cleaned_data["title"]

    class Meta(object):
        """Define the ThemeForm metadata."""

        model = Theme
        fields = "__all__"


class FrontThemeForm(ThemeForm):
    """Form class for Theme editing in front."""

    def __init__(self, *args, **kwargs) -> None:
        """Initialize a new FrontThemeForm instance."""
        self.THEME_FORM_FIELDS_HELP_TEXT = THEME_FORM_FIELDS_HELP_TEXT

        super(FrontThemeForm, self).__init__(*args, **kwargs)

        self.fields["channel"].widget = forms.HiddenInput()
        # self.fields["parentId"].label = _('Theme parent')
        # Add WYSIWYG when edit a theme
        self.fields["description"].widget = TinyMCE()
        for key, _value in settings.LANGUAGES:
            self.fields["description_%s" % key.replace("-", "_")].widget = TinyMCE()

        if "channel" in self.initial.keys():
            themes_queryset = Theme.objects.filter(channel=self.initial["channel"])
            self.fields["parentId"].queryset = themes_queryset

    class Meta(object):
        """Define the FrontThemeForm metadata."""

        model = Theme
        fields = "__all__"


class VideoPasswordForm(forms.Form):
    """Form class for video password."""

    password = forms.CharField(label=_("Password"), widget=forms.PasswordInput())

    def __init__(self, *args, **kwargs) -> None:
        """Initialize a new VideoPasswordForm instance."""
        super(VideoPasswordForm, self).__init__(*args, **kwargs)
        self.fields = add_placeholder_and_asterisk(self.fields)


class VideoDeleteForm(forms.Form):
    """Form class for video deletion."""

    agree = forms.BooleanField(
        label=_("I agree"),
        help_text=_("Delete video cannot be undo"),
        widget=forms.CheckboxInput(),
    )

    def __init__(self, *args, **kwargs) -> None:
        """Initialize a new VideoDeleteForm instance."""
        super(VideoDeleteForm, self).__init__(*args, **kwargs)
        self.fields = add_placeholder_and_asterisk(self.fields)


class TypeForm(forms.ModelForm):
    """Form class for Type editing."""

    def __init__(self, *args, **kwargs) -> None:
        """Initialize a new TypeForm instance."""
        super(TypeForm, self).__init__(*args, **kwargs)
        if __FILEPICKER__:
            self.fields["icon"].widget = CustomFileWidget(type="image")

    class Meta(object):
        """Define the TypeForm metadata."""

        model = Type
        fields = "__all__"


class DisciplineForm(forms.ModelForm):
    """Form class for Discipline editing."""

    def __init__(self, *args, **kwargs) -> None:
        """Initialize a new DisciplineForm instance."""
        super(DisciplineForm, self).__init__(*args, **kwargs)
        if __FILEPICKER__:
            self.fields["icon"].widget = CustomFileWidget(type="image")

    class Meta(object):
        """Define the DisciplineForm metadata."""

        model = Discipline
        fields = "__all__"


class VideoVersionForm(forms.ModelForm):
    """Form class for VideoVersion editing."""

    def __init__(self, *args, **kwargs) -> None:
        """Initialize a new VideoVersionForm instance."""
        super(VideoVersionForm, self).__init__(*args, **kwargs)

    class Meta(object):
        """Define the VideoVersionForm metadata."""

        model = VideoVersion
        fields = "__all__"


class NotesForm(forms.ModelForm):
    """Form class for Notes editing."""

    def __init__(self, *args, **kwargs) -> None:
        """Initialize a new NotesForm instance."""
        super(NotesForm, self).__init__(*args, **kwargs)
        # self.fields["user"].widget = forms.HiddenInput()
        # self.fields["video"].widget = forms.HiddenInput()
        # self.fields["note"].widget.attrs["cols"] = 20
        self.fields["note"].widget.attrs["class"] = "form-control"
        self.fields["note"].widget.attrs["rows"] = 5

    class Meta(object):
        """Define the NotesForm metadata."""

        model = Notes
        fields = ["note"]


class AdvancedNotesForm(forms.ModelForm):
    """Form class for AdvancedNotes editing."""

    def __init__(self, *args, **kwargs) -> None:
        """Initialize a new AdvancedNotesForm instance."""
        super(AdvancedNotesForm, self).__init__(*args, **kwargs)
        # self.fields["user"].widget = forms.HiddenInput()
        self.fields["video"].widget = forms.HiddenInput()
        self.fields["note"].widget.attrs["class"] = "form-control input_note"
        self.fields["note"].widget.attrs["autocomplete"] = "off"
        self.fields["note"].widget.attrs["rows"] = 3
        self.fields["note"].widget.attrs["cols"] = 20
        self.fields["note"].required = True
        self.fields["note"].help_text = _("A note can’t be empty")
        self.fields["timestamp"].widget = forms.HiddenInput()
        self.fields["timestamp"].widget.attrs["class"] = "form-control"
        self.fields["timestamp"].widget.attrs["autocomplete"] = "off"
        self.fields["status"].widget.attrs["class"] = "form-select"

    class Meta(object):
        """Define the AdvancedNotesForm metadata."""

        model = AdvancedNotes
        fields = ["video", "note", "timestamp", "status"]


class NoteCommentsForm(forms.ModelForm):
    """Form class for NoteComments editing."""

    def __init__(self, *args, **kwargs) -> None:
        """Initialize a new NoteCommentsForm instance."""
        super(NoteCommentsForm, self).__init__(*args, **kwargs)
        # self.fields["user"].widget = forms.HiddenInput()
        # self.fields["note"].widget = forms.HiddenInput()
        self.fields["comment"].widget.attrs[
            "class"
        ] = "form-control \
            input_comment"
        self.fields["comment"].widget.attrs["autocomplete"] = "off"
        self.fields["comment"].widget.attrs["rows"] = 3
        self.fields["comment"].widget.attrs["cols"] = 20
        self.fields["comment"].required = True
        self.fields["comment"].help_text = _("A comment can’t be empty")
        self.fields["status"].widget.attrs["class"] = "form-select"

    class Meta(object):
        """Define the NoteCommentsForm metadata."""

        model = NoteComments
        fields = ["comment", "status"]
