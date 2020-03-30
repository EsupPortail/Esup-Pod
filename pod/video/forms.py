from django import forms
from django.contrib.admin import widgets
from django.conf import settings
from django.core.validators import FileExtensionValidator
from django.utils.deconstruct import deconstructible
from django.utils.translation import ugettext_lazy as _
from django.template.defaultfilters import filesizeformat
from django.core.exceptions import ValidationError
from django.contrib.auth.models import User

from .models import Video, VideoVersion
from .models import Channel
from .models import Theme
from .models import Type
from .models import Discipline
from .models import Notes, AdvancedNotes, NoteComments
from .encode import start_encode
from .models import get_storage_path_video
from .models import EncodingVideo, EncodingAudio, PlaylistVideo


from django.dispatch import receiver
from django.db.models.signals import post_save

from pod.main.forms import add_placeholder_and_asterisk

from ckeditor.widgets import CKEditorWidget
from collections import OrderedDict

import datetime
import os
import re

FILEPICKER = False
if getattr(settings, 'USE_PODFILE', False):
    FILEPICKER = True
    from pod.podfile.widgets import CustomFileWidget

TRANSCRIPT = getattr(settings, 'USE_TRANSCRIPTION', False)

ENCODE_VIDEO = getattr(settings,
                       'ENCODE_VIDEO',
                       start_encode)

USE_OBSOLESCENCE = getattr(
    settings, "USE_OBSOLESCENCE", False)

VIDEO_ALLOWED_EXTENSIONS = getattr(
    settings, 'VIDEO_ALLOWED_EXTENSIONS', (
        '3gp',
        'avi',
        'divx',
        'flv',
        'm2p',
        'm4v',
        'mkv',
        'mov',
        'mp4',
        'mpeg',
        'mpg',
        'mts',
        'wmv',
        'mp3',
        'ogg',
        'wav',
        'wma',
        'webm',
        'ts'
    )
)
VIDEO_MAX_UPLOAD_SIZE = getattr(
    settings, 'VIDEO_MAX_UPLOAD_SIZE', 1)

VIDEO_FORM_FIELDS_HELP_TEXT = getattr(
    settings,
    'VIDEO_FORM_FIELDS_HELP_TEXT',
    OrderedDict([
        ("{0}".format(_("File field")), [
            _("You can send an audio or video file."),
            _("The following formats are supported: %s") %
            ', '.join(map(str, VIDEO_ALLOWED_EXTENSIONS))
        ]),
        ("{0}".format(_("Title field")), [
            _("Please choose a title as short and accurate as possible, "
                "reflecting the main subject / context of the content."),
            _("You can use the “Description” field below for all "
                "additional information."),
            _("You may add contributors later using the second button of "
              "the content edition toolbar: they will appear in the “Info” "
              "tab at the bottom of the audio / video player.")
        ]),
        ("{0}".format(_("Type")), [
            _("Select the type of your content. If the type you wish does "
                "not appear in the list, please temporary select “Other” "
                "and contact us to explain your needs.")
        ]),
        ("{0}".format(_("Additional owners")), [
            _("In this field you can select and add additional owners to the "
                "video. These additional owners will have the same rights as "
                "you except that they can't delete this video.")
        ]),
        ("{0}".format(_("Description")), [
            _("In this field you can describe your content, add all needed "
                "related information, and format the result "
                "using the toolbar.")
        ]),
        ("{0}".format(_("Date of the event field")), [
            _("Enter the date of the event, if applicable, in the "
                "AAAA-MM-JJ format.")
        ]),
        ("{0}".format(_("University course")), [
            _("Select an university course as audience target of "
                "the content."),
            _("Choose “None / All” if it does not apply or if all are "
                "concerned, or “Other” for an audience outside "
                "the european LMD scheme.")
        ]),
        ("{0}".format(_("Main language")), [
            _("Select the main language used in the content.")
        ]),
        ("{0}".format(_("Tags")), [
            _("Please try to add only relevant keywords that can be "
                "useful to other users.")
        ]),
        ("{0}".format(_("Disciplines")), [
            _("Select the discipline to which your content belongs. "
                "If the discipline you wish does not appear in the list, "
                "please select nothing and contact us to explain your needs."),
            _('Hold down "Control", or "Command" on a Mac, '
              'to select more than one.')
        ]),
        ("{0}".format(_("Licence")), [
            ('<a href="https://creativecommons.org/licenses/by/4.0/" '
                'title="%(lic)s" target="_blank">%(lic)s</a>') % {
                'lic':
                _("Attribution 4.0 International (CC BY 4.0)")},
            ('<a href="https://creativecommons.org/licenses/by-nd/4.0/" '
                'title="%(lic)s" target="_blank">%(lic)s</a>') % {
                'lic': _("Attribution-NoDerivatives 4.0 "
                         "International (CC BY-ND 4.0)")},
            ('<a href="https://creativecommons.org/licenses/by-nc-nd/4.0/" '
                'title="%(lic)s" target="_blank">%(lic)s</a>') % {
                'lic': _("Attribution-NonCommercial-NoDerivatives 4.0 "
                         "International (CC BY-NC-ND 4.0)")},
            ('<a href="https://creativecommons.org/licenses/by-nc/4.0/" '
                'title="%(lic)s" target="_blank">%(lic)s</a>') % {
                'lic': _("Attribution-NonCommercial 4.0 "
                         "International (CC BY-NC 4.0)")},
            ('<a href="https://creativecommons.org/licenses/by-nc-sa/4.0/" '
                'title="%(lic)s" target="_blank">%(lic)s</a>') % {
                'lic': _(
                    "Attribution-NonCommercial-ShareAlike 4.0 "
                    "International (CC BY-NC-SA 4.0)"
                )},
            ('<a href="https://creativecommons.org/licenses/by-sa/4.0/" '
                'title="%(lic)s" target="_blank">%(lic)s</a>') % {
                'lic': _(
                    "Attribution-ShareAlike 4.0 "
                    "International (CC BY-SA 4.0)")},
        ]),
        ("{0} / {1}".format(_("Channels"), _("Themes")), [
            _("Select the channel in which you want your content to appear."),
            _("Themes related to this channel will "
                "appear in the “Themes” list below."),
            _('Hold down "Control", or "Command" on a Mac, '
                'to select more than one.'),
            _("If the channel or Themes you wish does not appear "
                "in the list, please select nothing and contact "
                "us to explain your needs.")
        ]),
        ("{0}".format(_("Draft")), [
            _("In “Draft mode”, the content shows nowhere and nobody "
                "else but you can see it.")
        ]),
        ("{0}".format(_("Restricted access")), [
            _("If you don't select “Draft mode”, you can restrict "
                "the content access to only people who can log in")
        ]),
        ("{0}".format(_("Password")), [
            _("If you don't select “Draft mode”, you can add a password "
                "which will be asked to anybody willing to watch "
                "your content."),
            _("If your video is in a playlist the password of your "
                "video will be removed automatically.")
        ])
    ]))

if TRANSCRIPT:
    transcript_help_text = OrderedDict([
        ("{0}".format(_("Transcript")), [
            _("Available only in French and English, transcription is a speech"
              " recognition technology that transforms an oral speech into "
              "text in an automated way. By checking this box, it will "
              "generate a subtitle file automatically when encoding the video."
              ),
            _("You will probably have to modify this file using the "
              "captioning tool in the completion page to improve it.")
        ])])
    VIDEO_FORM_FIELDS_HELP_TEXT.update(transcript_help_text)

VIDEO_FORM_FIELDS = getattr(
    settings,
    'VIDEO_FORM_FIELDS', '__all__')


CHANNEL_FORM_FIELDS_HELP_TEXT = getattr(
    settings,
    'CHANNEL_FORM_FIELDS_HELP_TEXT',
    OrderedDict([
        ("{0}".format(_("Title field")), [
            _("Please choose a title as short and accurate as possible, "
                "reflecting the main subject / context of the content."),
            _("You can use the “Description” field below for all "
                "additional information.")
        ]),
        ("{0}".format(_("Description")), [
            _("In this field you can describe your content, add all needed "
                "related information, and format the result "
                "using the toolbar.")
        ]),
        (("{0} / {1}".format(_('Extra style'), _('Background color'))), [
            _("In this field you can add some style to personnalize "
                "your channel.")
        ]),
        (("{0} / {1}".format(_("Owners"), _('Users'))), [
            _("Owners can add videos to this channel "
                "and access this page to customize the channel."),
            _("Users can only add videos to this channel")
        ])
    ]))

THEME_FORM_FIELDS_HELP_TEXT = getattr(
    settings,
    'THEME_FORM_FIELDS_HELP_TEXT',
    OrderedDict([
        ("{0}".format(_("Title field")), [
            _("Please choose a title as short and accurate as possible, "
                "reflecting the main subject / context of the content."),
            _("You can use the “Description” field below for all "
                "additional information.")
        ]),
        ("{0}".format(_("Description")), [
            _("In this field you can describe your content, add all needed "
                "related information, and format the result "
                "using the toolbar.")
        ])
    ]))


@deconstructible
class FileSizeValidator(object):
    message = _(
        'The current file %(size)s, which is too large. '
        'The maximum file size is %(allowed_size)s.')
    code = 'invalid_max_size'

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
                    'size': filesizeformat(filesize),
                    'allowed_size': filesizeformat(self.max_size)
                })


@receiver(post_save, sender=Video)
def launch_encode(sender, instance, created, **kwargs):
    if hasattr(instance, 'launch_encode') and instance.launch_encode is True:
        instance.launch_encode = False
        ENCODE_VIDEO(instance.id)


class VideoForm(forms.ModelForm):
    required_css_class = 'required'
    videoattrs = {
        "class": "form-control-file",
        "accept": "audio/*, video/*, .%s" %
        ', .'.join(map(str, VIDEO_ALLOWED_EXTENSIONS)),
    }
    is_admin = False

    def move_video_source_file(self, new_path, new_dir, old_dir):
        # create user repository
        dest_file = os.path.join(
            settings.MEDIA_ROOT,
            new_path
        )
        os.makedirs(os.path.dirname(dest_file), exist_ok=True)
        # move video
        os.rename(os.path.join(
            settings.MEDIA_ROOT,
            self.cleaned_data['video'].name
        ), dest_file)
        # change path for video
        self.instance.video = new_path
        # Move Dir
        os.rename(
            os.path.join(settings.MEDIA_ROOT, old_dir),
            os.path.join(settings.MEDIA_ROOT, new_dir),
        )
        # Overview
        if self.instance.overview:
            self.instance.overview = self.instance.overview.name.replace(
                old_dir, new_dir)

    def change_encoded_path(self, video, new_dir, old_dir):
        encoding_video = EncodingVideo.objects.filter(
            video=video)
        for encoding in encoding_video:
            encoding.source_file = encoding.source_file.name.replace(
                old_dir, new_dir)
            encoding.save()
        encoding_audio = EncodingAudio.objects.filter(
            video=video)
        for encoding in encoding_audio:
            encoding.source_file = encoding.source_file.name.replace(
                old_dir, new_dir)
            encoding.save()
        playlist = PlaylistVideo.objects.filter(video=video)
        for encoding in playlist:
            encoding.source_file = encoding.source_file.name.replace(
                old_dir, new_dir)
            encoding.save()

    def save(self, commit=True, *args, **kwargs):
        old_dir = ""
        new_dir = ""
        if hasattr(self, 'change_user') and self.change_user is True:
            # create new video file
            storage_path = get_storage_path_video(
                self.instance,
                os.path.basename(self.cleaned_data['video'].name))
            dt = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            nom, ext = os.path.splitext(
                os.path.basename(self.cleaned_data['video'].name))
            ext = ext.lower()
            nom = re.sub(r'_\d{4}-\d{2}-\d{2}_\d{2}-\d{2}-\d{2}$', '', nom)
            new_path = os.path.join(
                os.path.dirname(storage_path),
                nom + "_" + dt + ext)
            if self.instance.overview:
                old_dir = os.path.dirname(self.instance.overview.name)
            else:
                old_dir = os.path.dirname(os.path.join(
                    self.cleaned_data['video'].name,
                    "%04d" % self.instance.id))
            new_dir = os.path.join(
                os.path.dirname(new_path), "%04d" % self.instance.id)
            self.move_video_source_file(new_path, new_dir, old_dir)

        video = super(VideoForm, self).save(commit, *args, **kwargs)

        if hasattr(self, 'change_user') and self.change_user is True:
            self.change_encoded_path(video, new_dir, old_dir)

        if hasattr(self, 'launch_encode'):
            video.launch_encode = self.launch_encode
        return video

    def clean(self):
        cleaned_data = super(VideoForm, self).clean()

        self.launch_encode = (
            'video' in cleaned_data.keys()
            and hasattr(self.instance, 'video')
            and cleaned_data['video'] != self.instance.video)

        self.change_user = (
            self.launch_encode is False
            and hasattr(self.instance, 'encoding_in_progress')
            and self.instance.encoding_in_progress is False
            and hasattr(self.instance, 'owner')
            and 'owner' in cleaned_data.keys()
            and cleaned_data['owner'] != self.instance.owner)

        if 'description' in cleaned_data.keys():
            cleaned_data['description_%s' %
                         settings.LANGUAGE_CODE
                         ] = cleaned_data['description']
        if 'title' in cleaned_data.keys():
            cleaned_data[
                'title_%s' %
                settings.LANGUAGE_CODE
            ] = cleaned_data['title']
        if ('restrict_access_to_groups' in cleaned_data.keys()
                and len(cleaned_data['restrict_access_to_groups']) > 0):
            cleaned_data['is_restricted'] = True

    def __init__(self, *args, **kwargs):

        self.is_staff = kwargs.pop(
            'is_staff') if 'is_staff' in kwargs.keys() else self.is_staff
        self.is_superuser = kwargs.pop(
            'is_superuser') if (
            'is_superuser' in kwargs.keys()
        ) else self.is_superuser

        self.current_user = kwargs.pop(
            'current_user') if kwargs.get('current_user') else None

        self.VIDEO_ALLOWED_EXTENSIONS = VIDEO_ALLOWED_EXTENSIONS
        self.VIDEO_MAX_UPLOAD_SIZE = VIDEO_MAX_UPLOAD_SIZE
        self.VIDEO_FORM_FIELDS_HELP_TEXT = VIDEO_FORM_FIELDS_HELP_TEXT

        super(VideoForm, self).__init__(*args, **kwargs)

        if FILEPICKER and self.fields.get('thumbnail'):
            self.fields['thumbnail'].widget = CustomFileWidget(type="image")

        if not TRANSCRIPT:
            self.remove_field('transcript')

        if self.fields.get('video'):
            self.fields['video'].label = _(u'File')
            valid_ext = FileExtensionValidator(VIDEO_ALLOWED_EXTENSIONS)
            self.fields['video'].validators = [valid_ext, FileSizeValidator]
            self.fields['video'].widget.attrs[
                'class'] = self.videoattrs["class"]
            self.fields['video'].widget.attrs[
                'accept'] = self.videoattrs["accept"]

        if self.instance.encoding_in_progress:
            self.remove_field('owner')
            self.remove_field('video')  # .widget = forms.HiddenInput()

        # change ckeditor, thumbnail and date delete config for no staff user
        self.set_nostaff_config()

        # hide default language
        self.hide_default_language()

        # QuerySet for channels and theme
        self.set_queryset()

        if self.is_superuser is False and self.is_admin is False:
            self.remove_field('date_added')
            self.remove_field('owner')

        self.fields = add_placeholder_and_asterisk(self.fields)

        # remove required=True for videofield if instance
        if self.fields.get('video') and self.instance and self.instance.video:
            del self.fields["video"].widget.attrs["required"]

    def set_nostaff_config(self):
        if self.is_staff is False:
            del self.fields['thumbnail']

            self.fields['description'].widget = CKEditorWidget(
                config_name='default')
            for key, value in settings.LANGUAGES:
                self.fields['description_%s' % key.replace(
                    '-', '_')].widget = CKEditorWidget(config_name='default')
        if self.fields.get('date_delete'):
            if (
                    self.is_staff is False
                    or self.instance.id is None
                    or USE_OBSOLESCENCE is False):
                del self.fields['date_delete']
            else:
                self.fields[
                    'date_delete'].widget = widgets.AdminDateWidget()

    def hide_default_language(self):
        if self.fields.get('description_%s' % settings.LANGUAGE_CODE):
            self.fields['description_%s' %
                        settings.LANGUAGE_CODE].widget = forms.HiddenInput()
        if self.fields.get('title_%s' % settings.LANGUAGE_CODE):
            self.fields['title_%s' %
                        settings.LANGUAGE_CODE].widget = forms.HiddenInput()

    def remove_field(self, field):
        if self.fields.get(field):
            del self.fields[field]

    def set_queryset(self):
        if self.current_user is not None:
            user_channels = Channel.objects.all() if self.is_superuser else (
                self.current_user.owners_channels.all(
                ) | self.current_user.users_channels.all()
            ).distinct()
            if user_channels:
                self.fields["channel"].queryset = user_channels
                list_theme = Theme.objects.filter(
                    channel__in=user_channels).order_by('channel', 'title')
                self.fields["theme"].queryset = list_theme
            else:
                # self.fields['channel'].widget = forms.HiddenInput()
                # self.fields['theme'].widget = forms.HiddenInput()
                del self.fields['theme']
                del self.fields['channel']

    class Meta(object):
        model = Video
        fields = VIDEO_FORM_FIELDS
        widgets = {
            # 'date_added': widgets.AdminSplitDateTime,
            'date_evt': widgets.AdminDateWidget,
        }
        initial = {
            'date_added': datetime.date.today,
            'date_evt': datetime.date.today,
        }


class ChannelForm(forms.ModelForm):
    users = forms.ModelMultipleChoiceField(
        User.objects.all(),
        widget=widgets.FilteredSelectMultiple(
            _("Users"),
            False,
            attrs={}),
        required=False,
        label=_('Users'))
    owners = forms.ModelMultipleChoiceField(
        User.objects.all(),
        widget=widgets.FilteredSelectMultiple(_("Owners"), False, attrs={}),
        required=False,
        label=_('Owners'))

    def clean(self):
        cleaned_data = super(ChannelForm, self).clean()
        if 'description' in cleaned_data.keys():
            cleaned_data['description_%s' %
                         settings.LANGUAGE_CODE
                         ] = cleaned_data['description']
        if 'title' in cleaned_data.keys():
            cleaned_data[
                'title_%s' %
                settings.LANGUAGE_CODE
            ] = cleaned_data['title']

    def __init__(self, *args, **kwargs):
        self.is_staff = kwargs.pop(
            'is_staff') if 'is_staff' in kwargs.keys() else self.is_staff
        self.is_superuser = kwargs.pop(
            'is_superuser') if (
            'is_superuser' in kwargs.keys()
        ) else self.is_superuser

        self.CHANNEL_FORM_FIELDS_HELP_TEXT = CHANNEL_FORM_FIELDS_HELP_TEXT

        super(ChannelForm, self).__init__(*args, **kwargs)
        if FILEPICKER:
            self.fields['headband'].widget = CustomFileWidget(type="image")

        if not hasattr(self, 'admin_form'):
            del self.fields['visible']

        # change ckeditor config for no staff user
        if not hasattr(self, 'admin_form') and (
                self.is_staff is False or self.is_superuser is False
        ):
            del self.fields['headband']
            self.fields['description'].widget = CKEditorWidget(
                config_name='default')
            for key, value in settings.LANGUAGES:
                self.fields['description_%s' % key.replace(
                    '-', '_')].widget = CKEditorWidget(config_name='default')
        # hide default langage
        self.fields['description_%s' %
                    settings.LANGUAGE_CODE].widget = forms.HiddenInput()
        self.fields['title_%s' %
                    settings.LANGUAGE_CODE].widget = forms.HiddenInput()

        self.fields = add_placeholder_and_asterisk(self.fields)

    class Meta(object):
        model = Channel
        fields = '__all__'


class ThemeForm(forms.ModelForm):

    def __init__(self, *args, **kwargs):
        super(ThemeForm, self).__init__(*args, **kwargs)
        if FILEPICKER:
            self.fields['headband'].widget = CustomFileWidget(type="image")

        # hide default langage
        self.fields['description_%s' %
                    settings.LANGUAGE_CODE].widget = forms.HiddenInput()
        self.fields['title_%s' %
                    settings.LANGUAGE_CODE].widget = forms.HiddenInput()

        self.fields = add_placeholder_and_asterisk(self.fields)

    def clean(self):
        cleaned_data = super(ThemeForm, self).clean()
        if 'description' in cleaned_data.keys():
            cleaned_data['description_%s' %
                         settings.LANGUAGE_CODE
                         ] = cleaned_data['description']
        if 'title' in cleaned_data.keys():
            cleaned_data[
                'title_%s' %
                settings.LANGUAGE_CODE
            ] = cleaned_data['title']

    class Meta(object):
        model = Theme
        fields = '__all__'


class FrontThemeForm(ThemeForm):

    def __init__(self, *args, **kwargs):

        self.THEME_FORM_FIELDS_HELP_TEXT = THEME_FORM_FIELDS_HELP_TEXT

        super(FrontThemeForm, self).__init__(*args, **kwargs)

        self.fields['channel'].widget = forms.HiddenInput()
        # self.fields["parentId"].label = _('Theme parent')
        if 'channel' in self.initial.keys():
            themes_queryset = Theme.objects.filter(
                channel=self.initial['channel'])
            self.fields["parentId"].queryset = themes_queryset

    class Meta(object):
        model = Theme
        fields = '__all__'


class VideoPasswordForm(forms.Form):
    password = forms.CharField(
        label=_('Password'),
        widget=forms.PasswordInput())

    def __init__(self, *args, **kwargs):
        super(VideoPasswordForm, self).__init__(*args, **kwargs)
        self.fields = add_placeholder_and_asterisk(self.fields)


class VideoDeleteForm(forms.Form):
    agree = forms.BooleanField(
        label=_('I agree'),
        help_text=_('Delete video cannot be undo'),
        widget=forms.CheckboxInput())

    def __init__(self, *args, **kwargs):
        super(VideoDeleteForm, self).__init__(*args, **kwargs)
        self.fields = add_placeholder_and_asterisk(self.fields)


class TypeForm(forms.ModelForm):

    def __init__(self, *args, **kwargs):
        super(TypeForm, self).__init__(*args, **kwargs)
        if FILEPICKER:
            self.fields['icon'].widget = CustomFileWidget(type="image")

    class Meta(object):
        model = Type
        fields = '__all__'


class DisciplineForm(forms.ModelForm):

    def __init__(self, *args, **kwargs):
        super(DisciplineForm, self).__init__(*args, **kwargs)
        if FILEPICKER:
            self.fields['icon'].widget = CustomFileWidget(type="image")

    class Meta(object):
        model = Discipline
        fields = '__all__'


class VideoVersionForm(forms.ModelForm):

    def __init__(self, *args, **kwargs):
        super(VideoVersionForm, self).__init__(*args, **kwargs)

    class Meta(object):
        model = VideoVersion
        fields = '__all__'


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
        self.fields["note"].help_text = _("A note can't be empty")
        self.fields["timestamp"].widget = forms.HiddenInput()
        self.fields["timestamp"].widget.attrs["class"] = "form-control"
        self.fields["timestamp"].widget.attrs["autocomplete"] = "off"
        self.fields["status"].widget.attrs["class"] = "form-control"

    class Meta(object):
        model = AdvancedNotes
        fields = ["video", "note", "timestamp", "status"]


class NoteCommentsForm(forms.ModelForm):

    def __init__(self, *args, **kwargs):
        super(NoteCommentsForm, self).__init__(*args, **kwargs)
        # self.fields["user"].widget = forms.HiddenInput()
        # self.fields["note"].widget = forms.HiddenInput()
        self.fields["comment"].widget.attrs["class"] = "form-control \
            input_comment"
        self.fields["comment"].widget.attrs["autocomplete"] = "off"
        self.fields["comment"].widget.attrs["rows"] = 3
        self.fields["comment"].widget.attrs["cols"] = 20
        self.fields["comment"].help_text = _("A comment can't be empty")
        self.fields["status"].widget.attrs["class"] = "form-control"

    class Meta(object):
        model = NoteComments
        fields = ["comment", "status"]
