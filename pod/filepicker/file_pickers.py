from django import forms
from django.core.files.base import ContentFile
from django.core.exceptions import NON_FIELD_ERRORS
from django.utils.translation import ugettext as _
from pod.filepicker.views import FilePickerBase
from pod.filepicker.views import ImagePickerBase
from pod.filepicker.models import CustomFileModel
from pod.filepicker.models import CustomImageModel
from pod.filepicker.models import UserDirectory
try:
    from pod.authentication.models import Owner
except ImportError:
    from django.contrib.auth.models import User as Owner

import pod.filepicker
import os


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
        if ext in ['.jpg', '.jpeg', '.png', '.gif', '.bmp']:
            raise forms.ValidationError(
                u'Image not allowed.')
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
        if ext not in ['.jpg', '.jpeg', '.png', '.gif', '.bmp']:
            raise forms.ValidationError(
                u'Must be a image.')
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
        owner = Owner.objects.get(id=user.id)
        return super(CustomFilePicker, self).get_files(
            search, owner, directory)

    def get_dirs(self, user, directory=None):
        owner = Owner.objects.get(id=user.id)
        queryset = self.structure.objects.filter(owner=owner)
        if not queryset:
            queryset = self.structure.objects.create(name='Home', owner=owner)
        return super(CustomFilePicker, self).get_dirs(user, directory)


class CustomImagePicker(ImagePickerBase):
    form = CustomImageForm
    columns = ('name', 'file_type', 'date_modified',)
    link_headers = ['Thumbnail', ]

    def get_files(self, search, user, directory):
        owner = Owner.objects.get(id=user.id)
        return super(CustomImagePicker, self).get_files(
            search, owner, directory)

    def get_dirs(self, user, directory=None):
        owner = Owner.objects.get(id=user.id)
        queryset = self.structure.objects.filter(owner=owner)
        if not queryset:
            self.structure.objects.create(name='Home', owner=owner)
        return super(CustomImagePicker, self).get_dirs(user, directory)


pod.filepicker.site.register(
    CustomFileModel,
    CustomFilePicker,
    name='file',
    structure=UserDirectory,
    configure=UserDirectoryForm)
pod.filepicker.site.register(
    CustomImageModel,
    CustomImagePicker,
    name='img',
    structure=UserDirectory,
    configure=UserDirectoryForm)
