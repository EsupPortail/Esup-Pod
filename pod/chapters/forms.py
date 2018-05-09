from django import forms
from django.apps import apps
from django.core.exceptions import ValidationError
from django.utils.safestring import mark_safe
from pod.chapters.models import Chapter
from pod.chapters.utils import vtt_to_chapter
if apps.is_installed('pod.filepicker'):
    FILEPICKER = True
    from pod.filepicker.models import CustomFileModel
    from pod.filepicker.widgets import CustomFilePickerWidget


class ChapterForm(forms.ModelForm):

    def __init__(self, *args, **kwargs):
        super(ChapterForm, self).__init__(*args, **kwargs)
        self.fields['video'].widget = forms.HiddenInput()
        self.fields['time_start'].widget.attrs['min'] = 0
        self.fields['time_end'].widget.attrs['min'] = 1
        try:
            self.fields['time_start'].widget.attrs[
                'max'] = self.instance.video.duration - 1
        except Exception:
            self.fields['time_start'].widget.attrs['max'] = 36000
            self.fields['time_end'].widget.attrs['max'] = 36000
        for myField in self.fields:
            self.fields[myField].widget.attrs[
                'placeholder'] = self.fields[myField].label
            if self.fields[myField].required:
                self.fields[myField].widget.attrs[
                    'class'] = 'form-control required'
                label_unicode = u'{0}'.format(self.fields[myField].label)
                self.fields[myField].label = mark_safe(
                    '{0} <span class=\"special_class\">*</span>'.format(
                        label_unicode))
            else:
                self.fields[myField].widget.attrs['class'] = 'form-control'

    class Meta:
        model = Chapter
        fields = '__all__'


class ChapterImportForm(forms.Form):
    if FILEPICKER:
        file = forms.ModelChoiceField(queryset=CustomFileModel.objects.all())
    else:
        file = forms.FileField()

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user')
        self.video = kwargs.pop('video')
        super(ChapterImportForm, self).__init__(*args, **kwargs)
        if FILEPICKER:
            pickers = {'file': "file"}
            self.fields['file'].widget = CustomFilePickerWidget(
                pickers=pickers)
            self.fields['file'].queryset = CustomFileModel.objects.filter(
                created_by=self.user)

    def clean_file(self):
        msg = vtt_to_chapter(self.cleaned_data['file'], self.video)
        if msg:
            raise ValidationError('Error ! {0}'.format(msg))
        return self.cleaned_data['file']