from django import forms
from django.contrib.admin import widgets
from django.contrib.auth.models import User
from django.conf import settings
from django.core.validators import FileExtensionValidator
from django.core.exceptions import ValidationError
from django.forms.widgets import ClearableFileInput
from django.utils.deconstruct import deconstructible
from django.utils.translation import ugettext_lazy as _
from django.template.defaultfilters import filesizeformat
from .models import Video, VideoVersion
from .models import Channel
from .models import Theme
from .models import Type
from .models import Discipline
from .models import Notes, AdvancedNotes, NoteComments
from .utils import get_storage_path_video
from pod.video_encode_transcript.models import PlaylistVideo
from pod.video_encode_transcript import encode
from pod.video_encode_transcript.models import EncodingVideo, EncodingAudio
from django.contrib.sites.models import Site
from django.db.models.query import QuerySet

from django.dispatch import receiver
from django.db.models.signals import post_save
from django.contrib.sites.shortcuts import get_current_site
from pod.main.forms_utils import add_placeholder_and_asterisk, add_describedby_attr

from ckeditor.widgets import CKEditorWidget
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

__TODAY__ = datetime.date.today()

__MAX_D__ = __TODAY__.replace(year=__TODAY__.year + MAX_DURATION_DATE_DELETE)

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
                        "you except that they can't delete this video."
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
                        '<a href="https://creativecommons.org/licenses/by/4.0/" '
                        'title="%(lic)s" target="_blank">%(lic)s</a>'
                    )
                    % {"lic": _("Attribution 4.0 International (CC BY 4.0)")},
                    (
                        '<a href="https://creativecommons.org/licenses/by-nd/4.0/" '
                        'title="%(lic)s" target="_blank">%(lic)s</a>'
                    )
                    % {
                        "lic": _(
                            "Attribution-NoDerivatives 4.0 "
                            "International (CC BY-ND 4.0)"
                        )
                    },
                    (
                        '<a href="https://creativecommons.org/licenses/by-nc-nd/4.0/" '
                        'title="%(lic)s" target="_blank">%(lic)s</a>'
                    )
                    % {
                        "lic": _(
                            "Attribution-NonCommercial-NoDerivatives 4.0 "
                            "International (CC BY-NC-ND 4.0)"
                        )
                    },
                    (
                        '<a href="https://creativecommons.org/licenses/by-nc/4.0/" '
                        'title="%(lic)s" target="_blank">%(lic)s</a>'
                    )
                    % {
                        "lic": _(
                            "Attribution-NonCommercial 4.0 "
                            "International (CC BY-NC 4.0)"
                        )
                    },
                    (
                        '<a href="https://creativecommons.org/licenses/by-nc-sa/4.0/" '
                        'title="%(lic)s" target="_blank">%(lic)s</a>'
                    )
                    % {
                        "lic": _(
                            "Attribution-NonCommercial-ShareAlike 4.0 "
                            "International (CC BY-NC-SA 4.0)"
                        )
                    },
                    (
                        '<a href="https://creativecommons.org/licenses/by-sa/4.0/" '
                        'title="%(lic)s" target="_blank">%(lic)s</a>'
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
                        "If the channel or Themes you wish does not appear "
                        "in the list, please select nothing and contact "
                        "us to explain your needs."
                    ),
                ],
            ),
            (
                "{0}".format(_("Draft")),
                [
                    _(
                        "In “Draft mode”, the content shows nowhere and nobody "
                        "else but you can see it."
                    )
                ],
            ),
            (
                "{0}".format(_("Restricted access")),
                [
                    _(
                        "If you don't select “Draft mode”, you can restrict "
                        "the content access to only people who can log in"
                    )
                ],
            ),
            (
                "{0}".format(_("Password")),
                [
                    _(
                        "If you don't select “Draft mode”, you can add a password "
                        "which will be asked to anybody willing to watch "
                        "your content."
                    ),
                    _(
                        "If your video is in a playlist the password of your "
                        "video will be removed automatically."
                    ),
                ],
            ),
        ]
    ),
)

if USE_TRANSCRIPTION:
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
    search_fields = [
        "username__icontains",
        "email__icontains",
    ]


class AddOwnerWidget(s2forms.ModelSelect2MultipleWidget):
    search_fields = [
        "username__icontains",
        "email__icontains",
    ]


class AddAccessGroupWidget(s2forms.ModelSelect2MultipleWidget):
    search_fields = [
        "display_name__icontains",
        "code_name__icontains",
    ]


class ChannelWidget(s2forms.ModelSelect2MultipleWidget):
    search_fields = [
        "title__icontains",
    ]


class DisciplineWidget(s2forms.ModelSelect2MultipleWidget):
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
    message = _(
        "The current file %(size)s, which is too large. "
        "The maximum file size is %(allowed_size)s."
    )
    code = "invalid_max_size"

    def __init__(self, *args, **kwargs):
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
def launch_encode(sender, instance, created, **kwargs):
    if hasattr(instance, "launch_encode") and instance.launch_encode is True:
        instance.launch_encode = False
        encode_video = getattr(encode, ENCODE_VIDEO)
        encode_video(instance.id)


class VideoForm(forms.ModelForm):
    """Form class for Video editing."""

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
                "fields": ["allow_downloading", "is_360", "disable_comment"],
            },
        ),
    )

    def filter_fields_admin(form):
        """Hide fields reserved for admins."""
        if form.is_superuser is False and form.is_admin is False:
            form.remove_field("date_added")
            form.remove_field("owner")

        if not hasattr(form, "admin_form"):
            form.remove_field("sites")

    def move_video_source_file(self, new_path, new_dir, old_dir):
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

    def change_encoded_path(self, video, new_dir, old_dir):
        """Change the path of encodings related to a video."""
        models_to_update = [EncodingVideo, EncodingAudio, PlaylistVideo]
        for model in models_to_update:
            encodings = model.objects.filter(video=video)
            for encoding in encodings:
                encoding.source_file = encoding.source_file.name.replace(old_dir, new_dir)
                encoding.save()

    def save(self, commit=True, *args, **kwargs):
        """Save video and launch encoding if relevant."""
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
        return video

    def clean_date_delete(self):
        """Validate 'date_delete' field."""
        mddd = MAX_DURATION_DATE_DELETE
        date_delete = self.cleaned_data["date_delete"]
        in_dt = relativedelta(date_delete, __TODAY__)
        if (
            (in_dt.years > mddd)
            or (in_dt.years == mddd and in_dt.months > 0)
            or (in_dt.years == mddd and in_dt.months == 0 and in_dt.days > 0)
        ):
            raise ValidationError(
                _(
                    "The date must be before or equal to %(date)s."
                    % {"date": __MAX_D__.strftime("%d-%m-%Y")}
                ),
                code="date_too_far",
            )
        if date_delete < __TODAY__:
            raise ValidationError(
                _("The deletion date can’t be earlier than today."),
                code="date_before_today",
            )
        return self.cleaned_data["date_delete"]

    def clean(self):
        """Validate Video form fields."""
        cleaned_data = super(VideoForm, self).clean()

        if "additional_owners" in cleaned_data.keys() and isinstance(
            self.cleaned_data["additional_owners"], QuerySet
        ):
            vidowner = (
                self.instance.owner
                if hasattr(self.instance, "owner")
                else cleaned_data["owner"]
                if "owner" in cleaned_data.keys()
                else self.current_user
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

    def __init__(self, *args, **kwargs):
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
        # change ckeditor, thumbnail and date delete config for non staff user
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
                self.remove_field("owner")
                self.remove_field("video")  # .widget = forms.HiddenInput()

        # remove required=True for videofield if instance
        if self.fields.get("video") and self.instance and self.instance.video:
            del self.fields["video"].widget.attrs["required"]
        if self.fields.get("owner"):
            self.fields["owner"].queryset = self.fields["owner"].queryset.filter(
                owner__sites=Site.objects.get_current()
            )

    def custom_video_form(self):
        if not ACTIVE_VIDEO_COMMENT:
            self.remove_field("disable_comment")

        if __FILEPICKER__ and self.fields.get("thumbnail"):
            self.fields["thumbnail"].widget = CustomFileWidget(type="image")

        if not USE_TRANSCRIPTION:
            self.remove_field("transcript")

    def manage_more_required_fields(self):
        """Set the required attribute to True for all VIDEO_REQUIRED_FIELDS."""
        for field in VIDEO_REQUIRED_FIELDS:
            # field exists, not hide
            if self.fields.get(field, None):
                self.fields[field].required = True

    def set_nostaff_config(self):
        if self.is_staff is False:
            del self.fields["thumbnail"]

            self.fields["description"].widget = CKEditorWidget(config_name="default")
            for key, value in settings.LANGUAGES:
                self.fields[
                    "description_%s" % key.replace("-", "_")
                ].widget = CKEditorWidget(config_name="default")
        if self.fields.get("date_delete"):
            if (
                self.is_staff is False
                or self.instance.id is None
                or USE_OBSOLESCENCE is False
            ):
                del self.fields["date_delete"]
            else:
                self.fields["date_delete"].widget = forms.DateInput(
                    format=("%Y-%m-%d"),
                    attrs={"type": "date"},
                )

    def hide_default_language(self):
        if self.fields.get("description_%s" % settings.LANGUAGE_CODE):
            self.fields[
                "description_%s" % settings.LANGUAGE_CODE
            ].widget = forms.HiddenInput()
        if self.fields.get("title_%s" % settings.LANGUAGE_CODE):
            self.fields["title_%s" % settings.LANGUAGE_CODE].widget = forms.HiddenInput()

    def remove_field(self, field):
        if self.fields.get(field):
            del self.fields[field]

    def set_queryset(self):
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
            "channel": ChannelWidget,
            "discipline": DisciplineWidget,
            "date_evt": widgets.AdminDateWidget,
            "video": CustomClearableFileInput
            # "restrict_access_to_groups": AddAccessGroupWidget
        }
        initial = {
            "date_added": __TODAY__,
            "date_evt": __TODAY__,
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
        ), (
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

    def clean(self):
        cleaned_data = super(ChannelForm, self).clean()
        if "description" in cleaned_data.keys():
            cleaned_data["description_%s" % settings.LANGUAGE_CODE] = cleaned_data[
                "description"
            ]
        if "title" in cleaned_data.keys():
            cleaned_data["title_%s" % settings.LANGUAGE_CODE] = cleaned_data["title"]

    def __init__(self, *args, **kwargs):
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

        # change ckeditor config for no staff user
        if not hasattr(self, "admin_form") and (
            self.is_staff is False and self.is_superuser is False
        ):
            del self.fields["headband"]
            self.fields["description"].widget = CKEditorWidget(config_name="default")
            for key, value in settings.LANGUAGES:
                self.fields[
                    "description_%s" % key.replace("-", "_")
                ].widget = CKEditorWidget(config_name="default")
        # hide default langage
        self.fields[
            "description_%s" % settings.LANGUAGE_CODE
        ].widget = forms.HiddenInput()
        self.fields["title_%s" % settings.LANGUAGE_CODE].widget = forms.HiddenInput()

        self.fields = add_placeholder_and_asterisk(self.fields)
        self.fields = add_describedby_attr(self.fields)

    class Meta(object):
        model = Channel
        fields = "__all__"
        widgets = {
            "owners": AddOwnerWidget,
            "users": AddOwnerWidget,
            "allow_to_groups": AddAccessGroupWidget,
        }


class ThemeForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super(ThemeForm, self).__init__(*args, **kwargs)
        if __FILEPICKER__:
            self.fields["headband"].widget = CustomFileWidget(type="image")

        # hide default langage
        self.fields[
            "description_%s" % settings.LANGUAGE_CODE
        ].widget = forms.HiddenInput()
        self.fields["title_%s" % settings.LANGUAGE_CODE].widget = forms.HiddenInput()

        self.fields = add_placeholder_and_asterisk(self.fields)

    def clean(self):
        cleaned_data = super(ThemeForm, self).clean()
        if "description" in cleaned_data.keys():
            cleaned_data["description_%s" % settings.LANGUAGE_CODE] = cleaned_data[
                "description"
            ]
        if "title" in cleaned_data.keys():
            cleaned_data["title_%s" % settings.LANGUAGE_CODE] = cleaned_data["title"]

    class Meta(object):
        model = Theme
        fields = "__all__"


class FrontThemeForm(ThemeForm):
    def __init__(self, *args, **kwargs):
        self.THEME_FORM_FIELDS_HELP_TEXT = THEME_FORM_FIELDS_HELP_TEXT

        super(FrontThemeForm, self).__init__(*args, **kwargs)

        self.fields["channel"].widget = forms.HiddenInput()
        # self.fields["parentId"].label = _('Theme parent')
        if "channel" in self.initial.keys():
            themes_queryset = Theme.objects.filter(channel=self.initial["channel"])
            self.fields["parentId"].queryset = themes_queryset

    class Meta(object):
        model = Theme
        fields = "__all__"


class VideoPasswordForm(forms.Form):
    password = forms.CharField(label=_("Password"), widget=forms.PasswordInput())

    def __init__(self, *args, **kwargs):
        super(VideoPasswordForm, self).__init__(*args, **kwargs)
        self.fields = add_placeholder_and_asterisk(self.fields)


class VideoDeleteForm(forms.Form):
    agree = forms.BooleanField(
        label=_("I agree"),
        help_text=_("Delete video cannot be undo"),
        widget=forms.CheckboxInput(),
    )

    def __init__(self, *args, **kwargs):
        super(VideoDeleteForm, self).__init__(*args, **kwargs)
        self.fields = add_placeholder_and_asterisk(self.fields)


class TypeForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super(TypeForm, self).__init__(*args, **kwargs)
        if __FILEPICKER__:
            self.fields["icon"].widget = CustomFileWidget(type="image")

    class Meta(object):
        model = Type
        fields = "__all__"


class DisciplineForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super(DisciplineForm, self).__init__(*args, **kwargs)
        if __FILEPICKER__:
            self.fields["icon"].widget = CustomFileWidget(type="image")

    class Meta(object):
        model = Discipline
        fields = "__all__"


class VideoVersionForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super(VideoVersionForm, self).__init__(*args, **kwargs)

    class Meta(object):
        model = VideoVersion
        fields = "__all__"


class NotesForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super(NotesForm, self).__init__(*args, **kwargs)
        # self.fields["user"].widget = forms.HiddenInput()
        # self.fields["video"].widget = forms.HiddenInput()
        # self.fields["note"].widget.attrs["cols"] = 20
        self.fields["note"].widget.attrs["class"] = "form-control"
        self.fields["note"].widget.attrs["rows"] = 5

    class Meta(object):
        model = Notes
        fields = ["note"]


class AdvancedNotesForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super(AdvancedNotesForm, self).__init__(*args, **kwargs)
        # self.fields["user"].widget = forms.HiddenInput()
        self.fields["video"].widget = forms.HiddenInput()
        self.fields["note"].widget.attrs["class"] = "form-control input_note"
        self.fields["note"].widget.attrs["autocomplete"] = "off"
        self.fields["note"].widget.attrs["rows"] = 3
        self.fields["note"].widget.attrs["cols"] = 20
        self.fields["note"].required = True
        self.fields["note"].help_text = _("A note can't be empty")
        self.fields["timestamp"].widget = forms.HiddenInput()
        self.fields["timestamp"].widget.attrs["class"] = "form-control"
        self.fields["timestamp"].widget.attrs["autocomplete"] = "off"
        self.fields["status"].widget.attrs["class"] = "form-select"

    class Meta(object):
        model = AdvancedNotes
        fields = ["video", "note", "timestamp", "status"]


class NoteCommentsForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
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
        self.fields["comment"].help_text = _("A comment can't be empty")
        self.fields["status"].widget.attrs["class"] = "form-select"

    class Meta(object):
        model = NoteComments
        fields = ["comment", "status"]
