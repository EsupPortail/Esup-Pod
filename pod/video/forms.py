from django import forms
from django.contrib.admin import widgets
from django.conf import settings
from django.utils.safestring import mark_safe
from django.core.validators import FileExtensionValidator
from django.utils.deconstruct import deconstructible
from django.utils.translation import ugettext_lazy as _
from django.template.defaultfilters import filesizeformat
from django.core.exceptions import ValidationError

from django.contrib.auth.models import User

from pod.filepicker.widgets import CustomFilePickerWidget
from pod.video.models import Video
from pod.video.models import Channel
from pod.video.models import Theme
from pod.video.models import Type
from pod.video.models import Discipline

from ckeditor.widgets import CKEditorWidget
from collections import OrderedDict

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
        'wma'
    )
)
VIDEO_MAX_UPLOAD_SIZE = getattr(
    settings, 'VIDEO_MAX_UPLOAD_SIZE', 1)

VIDEO_FORM_FIELDS_HELP_TEXT = getattr(
    settings,
    'VIDEO_FORM_FIELDS_HELP_TEXT',
    OrderedDict([
        (_("File field"), [
            _("You can send an audio or video file."),
            _("The following formats are supported: %s" %
              ', '.join(map(str, VIDEO_ALLOWED_EXTENSIONS)))
        ]),
        (_("Title field"), [
            _("Please choose a title as short and accurate as possible, "
                "reflecting the main subject / context of the content."),
            _("You can use the “Description” field below for all "
                "additional information."),
            _("You may add contributors later using the second button of "
              "the content edition toolbar: they will appear in the “Info” "
              "tab at the bottom of the audio / video player.")
        ]),
        (_("Date of the event field"), [
            _("Enter the date of the event, if applicable, in the "
                "AAAA-MM-JJ format.")
        ]),
        (_("University course"), [
            _("Select an university course as audience target of "
                "the content."),
            _("Choose “None / All” if it does not apply or if all are "
                "concerned, or “Other” for an audience outside "
                "the european LMD scheme.")
        ]),
        (_("Main language"), [
            _("Select the main language used in the content.")
        ]),
        (_("Description"), [
            _("In this field you can describe your content, add all needed "
                "related information, and format the result "
                "using the toolbar.")
        ]),
        (_("Type"), [
            _("Select the type of your content. If the type you wish does "
                "not appear in the list, please temporary select “Other” "
                "and contact us to explain your needs.")
        ]),
        (_("Disciplines"), [
            _("Select the discipline to which your content belongs. "
                "If the discipline you wish does not appear in the list, "
                "please select nothing and contact us to explain your needs."),
            _('Hold down "Control", or "Command" on a Mac, '
              'to select more than one.')
        ]),
        (_("Channels / Themes"), [
            _("Select the channel in which you want your content to appear."),
            _("Themes related to this channel will "
                "appear in the “Themes” list below."),
            _('Hold down "Control", or "Command" on a Mac, '
                'to select more than one.'),
            _("If the channel or Themes you wish does not appear "
                "in the list, please select nothing and contact "
                "us to explain your needs.")
        ]),
        (_("Draft"), [
            _("In “Draft mode”, the content shows nowhere and nobody "
                "else but you can see it.")
        ]),
        (_("Restricted access"), [
            _("If you don't select “Draft mode”, you can restrict "
                "the content access to only people who can log in")
        ]),
        (_("Password"), [
            _("If you don't select “Draft mode”, you can add a password "
                "which will be asked to anybody willing to watch "
                "your content."),
            _("If your video is in a playlist the password of your "
                "video will be removed automatically.")
        ]),
        (_("Tags"), [
            _("Please try to add only relevant keywords that can be "
                "useful to other users.")
        ])
    ]))


CHANNEL_FORM_FIELDS_HELP_TEXT = getattr(
    settings,
    'CHANNEL_FORM_FIELDS_HELP_TEXT',
    OrderedDict([
        (_("Title field"), [
            _("Please choose a title as short and accurate as possible, "
                "reflecting the main subject / context of the content."),
            _("You can use the “Description” field below for all "
                "additional information.")
        ]),
        (_("Description"), [
            _("In this field you can describe your content, add all needed "
                "related information, and format the result "
                "using the toolbar.")
        ]),
        (("%s / %s" % (_('Extra style'), _('Background color'))), [
            _("In this field you can add some style to personnalize "
                "your channel.")
        ]),
        (("%s / %s" % (_("Owners"), _('Users'))), [
            _("Owners can add videos to this channel "
                "and access this page to customize the channel."),
            _("Users can only add videos to this channel")
        ])
    ]))

THEME_FORM_FIELDS_HELP_TEXT = getattr(
    settings,
    'THEME_FORM_FIELDS_HELP_TEXT',
    OrderedDict([
        (_("Title field"), [
            _("Please choose a title as short and accurate as possible, "
                "reflecting the main subject / context of the content."),
            _("You can use the “Description” field below for all "
                "additional information.")
        ]),
        (_("Description"), [
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


class VideoForm(forms.ModelForm):
    required_css_class = 'required'
    videoattrs = {
        "class": "form-control-file",
        "accept": "audio/*, video/*, .%s" %
        ', .'.join(map(str, VIDEO_ALLOWED_EXTENSIONS)),
    }
    video = forms.FileField(label=_(u'File'))

    def clean(self):
        cleaned_data = super(VideoForm, self).clean()
        cleaned_data['description_%s' %
                     settings.LANGUAGE_CODE
                     ] = cleaned_data['description']
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

        self.current_user = kwargs.pop(
            'current_user') if kwargs.get('current_user') else None

        self.VIDEO_ALLOWED_EXTENSIONS = VIDEO_ALLOWED_EXTENSIONS
        self.VIDEO_MAX_UPLOAD_SIZE = VIDEO_MAX_UPLOAD_SIZE
        self.VIDEO_FORM_FIELDS_HELP_TEXT = VIDEO_FORM_FIELDS_HELP_TEXT

        super(VideoForm, self).__init__(*args, **kwargs)

        pickers = {'image': "img"}
        self.fields['thumbnail'].widget = CustomFilePickerWidget(
            pickers=pickers)

        # fields['video'].widget = widgets.AdminFileWidget(attrs=videoattrs)
        valid_ext = FileExtensionValidator(VIDEO_ALLOWED_EXTENSIONS)
        self.fields['video'].validators = [valid_ext, FileSizeValidator]
        self.fields['video'].widget.attrs['class'] = self.videoattrs["class"]
        self.fields['video'].widget.attrs['accept'] = self.videoattrs["accept"]

        if self.instance.encoding_in_progress:
            del self.fields['video']

        # change ckeditor config for no staff user
        if self.is_staff is False:
            del self.fields['thumbnail']
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

        # QuerySet for channels and theme
        self.set_queryset()

        if not self.is_superuser:
            del self.fields['date_added']
            del self.fields['owner']

        self.fields = add_placeholder_and_asterisk(self.fields)
        # remove required=True for videofield if instance
        if self.fields.get('video') and self.instance and self.instance.video:
            del self.fields["video"].widget.attrs["required"]

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
                del self.fields['channel']
                del self.fields['theme']

    class Meta(object):
        model = Video
        fields = '__all__'
        widgets = {'date_added': widgets.AdminDateWidget,
                   'date_evt': widgets.AdminDateWidget,
                   }


def add_placeholder_and_asterisk(fields):
    for myField in fields:
        classname = fields[myField].widget.__class__.__name__
        if classname == 'CheckboxInput':
            if fields[myField].widget.attrs.get('class'):
                fields[myField].widget.attrs[
                    'class'] += ' form-check-input'
            else:
                fields[myField].widget.attrs[
                    'class'] = 'form-check-input '
        else:
            fields[myField].widget.attrs[
                'placeholder'] = fields[myField].label
            if fields[myField].required:
                fields[myField].label = mark_safe(
                    "%s <span class=\"required\">*</span>" %
                    fields[myField].label
                )
                fields[myField].widget.attrs["required"] = "true"
            if fields[myField].widget.attrs.get('class'):
                fields[myField].widget.attrs[
                    'class'] += ' form-control'
            else:
                fields[myField].widget.attrs[
                    'class'] = 'form-control '
    return fields


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
        cleaned_data['description_%s' %
                     settings.LANGUAGE_CODE
                     ] = cleaned_data['description']
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
        pickers = {'image': "img"}
        self.fields['headband'].widget = CustomFilePickerWidget(
            pickers=pickers)

        if not hasattr(self, 'admin_form'):
            del self.fields['visible']

        # change ckeditor config for no staff user
        if self.is_staff is False or self.is_superuser is False:
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
        pickers = {'image': "img"}
        self.fields['headband'].widget = CustomFilePickerWidget(
            pickers=pickers)

        # hide default langage
        self.fields['description_%s' %
                    settings.LANGUAGE_CODE].widget = forms.HiddenInput()
        self.fields['title_%s' %
                    settings.LANGUAGE_CODE].widget = forms.HiddenInput()

        self.fields = add_placeholder_and_asterisk(self.fields)

    def clean(self):
        cleaned_data = super(ThemeForm, self).clean()
        cleaned_data['description_%s' %
                     settings.LANGUAGE_CODE
                     ] = cleaned_data['description']
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
        pickers = {'image': "img"}
        self.fields['headband'].widget = CustomFilePickerWidget(
            pickers=pickers)

        self.fields['channel'].widget = forms.HiddenInput()
        # self.fields["parentId"].label = _('Theme parent')
        if 'channel' in self.initial.keys():
            themes_queryset = Theme.objects.filter(
                channel=self.initial['channel'])
            self.fields["parentId"].queryset = themes_queryset

    class Meta(object):
        model = Theme
        fields = '__all__'


class TypeForm(forms.ModelForm):

    def __init__(self, *args, **kwargs):
        super(TypeForm, self).__init__(*args, **kwargs)
        pickers = {'image': "img"}
        self.fields['icon'].widget = CustomFilePickerWidget(
            pickers=pickers)

    class Meta(object):
        model = Type
        fields = '__all__'


class DisciplineForm(forms.ModelForm):

    def __init__(self, *args, **kwargs):
        super(DisciplineForm, self).__init__(*args, **kwargs)
        pickers = {'image': "img"}
        self.fields['icon'].widget = CustomFilePickerWidget(
            pickers=pickers)

    class Meta(object):
        model = Discipline
        fields = '__all__'
