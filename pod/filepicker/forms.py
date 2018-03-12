"""
Forms for filepicker
Override FileForm and ImageForm from file_picker.uploads

django-file-picker : 0.9.1.
"""
from django import forms
from django.core.files.base import ContentFile
from .models import CustomFileModel, CustomImageModel

import os


class CustomFileForm(forms.ModelForm):
    file = forms.CharField(widget=forms.widgets.HiddenInput())

    class Meta(object):
        model = CustomFileModel
        fields = ('name', 'created_by', 'description')

    def __init__(self, *args, **kwargs):
        super(CustomFileForm, self).__init__(*args, **kwargs)
        self.fields['created_by'].disabled = True

    def save(self, commit=True):
        file = super(CustomFileForm, self).save(commit=False)
        file_path = os.path.basename(self.cleaned_data['file'])
        fh = ContentFile(open(self.cleaned_data['file'], 'rb').read())
        file.file.save(file_path, fh)
        if commit:
            file.save()
        return file


class CustomImageForm(forms.ModelForm):
    file = forms.CharField(widget=forms.widgets.HiddenInput())

    class Meta(object):
        model = CustomImageModel
        fields = ('name', 'created_by', 'description')

    def __init__(self, *args, **kwargs):
        super(CustomImageForm, self).__init__(*args, **kwargs)
        self.fields['created_by'].disabled = True

    def save(self, commit=True):
        image = super(CustomImageForm, self).save(commit=False)
        file_path = os.path.basename(self.cleaned_data['file'])
        fh = ContentFile(open(self.cleaned_data['file'], 'rb').read())
        image.file.save(file_path, fh)
        if commit:
            image.save()
        return image
