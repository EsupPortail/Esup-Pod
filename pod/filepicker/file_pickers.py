from django import forms
from django.conf import settings
from django.core.files.base import ContentFile
from django.core.exceptions import NON_FIELD_ERRORS
from django.utils.translation import ugettext as _
from pod.filepicker.views import FilePickerBase
from pod.filepicker.views import ImagePickerBase
from pod.filepicker.models import CustomFileModel
from pod.filepicker.models import CustomImageModel
from pod.filepicker.models import UserDirectory

from pod.filepicker.sites import site
import os

FILE_ALLOWED_EXTENSIONS = getattr(
    settings, 'FILE_ALLOWED_EXTENSIONS', (
        '.doc',
        '.docx',
        '.odt',
        '.pdf',
        '.xls',
        '.xlsx',
        '.ods',
        '.ppt',
        '.pptx',
        '.txt',
        '.html',
        '.htm',
        '.vtt',
        '.srt',
    )
)
IMAGE_ALLOWED_EXTENSIONS = getattr(
    settings, 'IMAGE_ALLOWED_EXTENSIONS', (
        '.jpg',
        '.jpeg',
        '.bmp',
        '.png',
        '.gif',
        '.tiff',
    )
)


class UserDirectoryForm(forms.ModelForm):

    class Meta(object):
        model = UserDirectory
        fields = ('name', 'owner', 'parent',)
        labels = {
            'name': _('Name'),
        }
        error_messages = {
            NON_FIELD_ERRORS: {
                'unique_together':
                    _('A directory with this name already exist' +
                        ' in this directory'),
            }
        }

    def __init__(self, *args, **kwargs):
        super(UserDirectoryForm, self).__init__(*args, **kwargs)
        self.fields['owner'].widget = forms.HiddenInput()
        self.fields['parent'].widget = forms.HiddenInput()


class CustomFileForm(forms.ModelForm):
    file = forms.CharField(
        widget=forms.widgets.HiddenInput(),
        label='File')

    class Meta(object):
        model = CustomFileModel
        fields = ('name', 'directory', 'created_by', 'description')
        labels = {
            'name': _('Name'),
            'directory': _('Directory'),
            'description': _('Description'),
        }

    def __init__(self, *args, **kwargs):
        super(CustomFileForm, self).__init__(*args, **kwargs)
        self.fields['created_by'].widget = forms.HiddenInput()
        self.fields['directory'].disabled = True

    def clean_file(self):
        name, ext = os.path.splitext(self.cleaned_data['file'])
        if ext not in FILE_ALLOWED_EXTENSIONS:
            raise forms.ValidationError(
                _('File type not allowed : {0}'.format(ext)))
        return self.cleaned_data['file']

    def save(self, commit=True):
        file = super(CustomFileForm, self).save(commit=False)
        file_path = os.path.basename(self.cleaned_data['file'])
        fh = ContentFile(open(self.cleaned_data['file'], 'rb').read())
        file.file.save(file_path, fh)
        if commit:
            file.save()
        return file


class CustomImageForm(forms.ModelForm):
    file = forms.CharField(
        widget=forms.widgets.HiddenInput(),
        label='Image')

    class Meta(object):
        model = CustomImageModel
        fields = ('name', 'directory', 'created_by', 'description')
        labels = {
            'name': _('Name'),
            'directory': _('Directory'),
            'description': _('Description'),
        }

    def __init__(self, *args, **kwargs):
        super(CustomImageForm, self).__init__(*args, **kwargs)
        self.fields['created_by'].widget = forms.HiddenInput()
        self.fields['directory'].disabled = True

    def clean_file(self):
        name, ext = os.path.splitext(self.cleaned_data['file'])
        if ext not in IMAGE_ALLOWED_EXTENSIONS:
            raise forms.ValidationError(
                _('File type not allowed : {0}'.format(ext)))
        return self.cleaned_data['file']

    def save(self, commit=True):
        image = super(CustomImageForm, self).save(commit=False)
        file_path = os.path.basename(self.cleaned_data['file'])
        fh = ContentFile(open(self.cleaned_data['file'], 'rb').read())
        image.file.save(file_path, fh)
        if commit:
            image.save()
        return image


class CustomFilePicker(FilePickerBase):
    form = CustomFileForm
    columns = ('name', 'file_type', 'date_modified',)
    extra_headers = ('Name', 'File type', 'Date modified', 'Delete')

    def get_files(self, search, user, directory):
        return super(CustomFilePicker, self).get_files(
            search, user, directory)

    def get_dirs(self, user, directory=None):
        queryset = self.structure.objects.filter(owner=user, name='Home')
        if not queryset:
            queryset = self.structure.objects.create(name='Home', owner=user)
        return super(CustomFilePicker, self).get_dirs(user, directory)


class CustomImagePicker(ImagePickerBase):
    form = CustomImageForm
    columns = ('name', 'file_type', 'date_modified',)
    link_headers = ['Thumbnail', ]

    def get_files(self, search, user, directory):
        return super(CustomImagePicker, self).get_files(
            search, user, directory)

    def get_dirs(self, user, directory=None):
        queryset = self.structure.objects.filter(owner=user, name='Home')
        if not queryset:
            self.structure.objects.create(name='Home', owner=user)
        return super(CustomImagePicker, self).get_dirs(user, directory)


site.register(
    CustomFileModel,
    CustomFilePicker,
    name='file',
    structure=UserDirectory,
    configure=UserDirectoryForm)

site.register(
    CustomImageModel,
    CustomImagePicker,
    name='img',
    structure=UserDirectory,
    configure=UserDirectoryForm)
