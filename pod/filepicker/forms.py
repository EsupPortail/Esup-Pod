"""
Forms for filepicker
Override FileForm and ImageForm from file_picker.uploads

django-file-picker : 0.9.1.
"""
from django import forms
from django.core.files.base import ContentFile
from django.utils.translation import ugettext as _

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
