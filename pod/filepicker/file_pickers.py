from django import forms
from django.core.files.base import ContentFile
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
        fields = ('name', 'owner', 'parent')
        labels = {
            'name': _('Name'),
            'owner': _('Owner'),
        }

    def __init__(self, *args, **kwargs):
        super(UserDirectoryForm, self).__init__(*args, **kwargs)
        self.fields['parent'].widget = forms.HiddenInput()
        self.fields['owner'].widget = forms.HiddenInput()


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

    def __init__(self, form_data, *args, **kwargs):
        super(CustomImageForm, self).__init__(*args, **kwargs)
        self.fields['created_by'].widget = forms.HiddenInput()
        self.fields['directory'].queryset = UserDirectory.objects.filter(
            users=form_data['user'].id, parent__name=form_data['directory'])

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

    def get_files(self, search, user, directory=None):
        owner = Owner.objects.get(id=user.id)
        directory = directory.name if directory else 'Home'
        return super(CustomImagePicker, self).get_files(
            search, owner, directory)

    def get_dirs(self, user):
        owner = Owner.objects.get(id=user.id)
        queryset = self.structure.objects.filter(owner=owner)
        if not queryset:
            queryset = self.structure.objects.create(
                name='Home',
                owner=owner)
        return super(CustomFilePicker, self).get_dirs(user)


class CustomImagePicker(ImagePickerBase):
    form = CustomImageForm
    columns = ('name', 'file_type', 'date_modified',)
    link_headers = ['Thumbnail', ]

    def get_files(self, search, user, directory='Home', shared=None):
        owner = Owner.objects.get(id=user.id)
        dirs = self.get_dirs(user, directory, shared)
        return super(CustomImagePicker, self).get_files(
            search, owner, directory)

    def get_dirs(self, user, directory, shared=None):
        owner = Owner.objects.get(id=user.id)
        queryset = self.structure.objects.filter(owner=owner)
        if not queryset:
            return self.structure.objects.create(
                name='Home',
                owner=owner)
        return super(CustomImagePicker, self).get_dirs(
            user, directory, shared)


pod.filepicker.site.register(
    CustomFileModel,
    CustomFilePicker,
    name='file',
    structure=UserDirectory)
pod.filepicker.site.register(
    CustomImageModel,
    CustomImagePicker,
    name='img',
    structure=UserDirectory,
    configure=UserDirectoryForm)
