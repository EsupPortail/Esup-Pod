"""
Forms for filepicker
Override FileForm and ImageForm from file_picker.uploads

django-file-picker : 0.9.1.
"""
from django import forms
from django.core.files.base import ContentFile
from django.utils.translation import ugettext as _
from pod.filepicker.models import CustomFileModel
from pod.filepicker.models import CustomImageModel

import os


class AjaxItemForm(forms.ModelForm):
    file = forms.CharField(
        widget=forms.widgets.HiddenInput(),
        label='File')

    def clean_file(self):
        file = self.cleaned_data['file']
        if not os.path.exists(file):
            raise forms.ValidationError('Missing file')
        return file

    def save(self, *args, **kwargs):
        item = super(AjaxItemForm, self).save(commit=False)
        filename = os.path.basename(self.cleaned_data['file'])
        getattr(item, self.Meta.exclude[0]).save(
            filename,
            ContentFile(open(str(self.cleaned_data['file']), 'rb').read())
        )
        item.save(*args, **kwargs)
        return item


class QueryForm(forms.Form):
    page = forms.IntegerField(min_value=0, required=False)
    search = forms.CharField(max_length=300, required=False)

    def clean_page(self):
        page = self.cleaned_data.get('image')
        return page or 1


class CustomFileForm(forms.ModelForm):
    file = forms.CharField(
        widget=forms.widgets.HiddenInput(),
        label='File')

    class Meta(object):
        model = CustomFileModel
        fields = ('name', 'created_by', 'description')
        labels = {
            'name': _('Name'),
            'created_by': _('Author'),
            'description': _('Description'),
        }

    def __init__(self, *args, **kwargs):
        super(CustomFileForm, self).__init__(*args, **kwargs)
        self.fields['created_by'].disabled = True

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
