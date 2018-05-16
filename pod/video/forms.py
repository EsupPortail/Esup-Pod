from django import forms
from django.contrib.admin import widgets
from pod.filepicker.widgets import CustomFilePickerWidget
from django.utils.safestring import mark_safe
from pod.video.models import Video
from pod.video.models import Channel
from pod.video.models import Theme
from pod.video.models import Type
from pod.video.models import Discipline

from ckeditor.widgets import CKEditorWidget


class VideoForm(forms.ModelForm):
    required_css_class = 'required'

    def __init__(self, *args, **kwargs):
        self.is_staff = kwargs.pop('is_staff')
        self.is_superuser = kwargs.pop('is_superuser')
        super(VideoForm, self).__init__(*args, **kwargs)
        pickers = {'image': "img"}
        self.fields['thumbnail'].widget = CustomFilePickerWidget(
            pickers=pickers)

        self.fields['video'].widget = widgets.AdminFileWidget(attrs={
            'class': 'form-control-file'})
        self.fields['description'].widget = CKEditorWidget(config_name='default')
        self.fields['description_fr'].widget = CKEditorWidget(config_name='default')

        for myField in self.fields:
            if self.fields[myField].widget.__class__.__name__ == 'CheckboxInput':
                if self.fields[myField].widget.attrs.get('class') :
                    self.fields[myField].widget.attrs['class'] += ' form-check-input'
                else:
                    self.fields[myField].widget.attrs['class'] = 'form-check-input '
            else:
                self.fields[myField].widget.attrs['placeholder'] = self.fields[myField].label
                if self.fields[myField].required:
                    self.fields[myField].label = mark_safe("%s <span class=\"special_class\">*</span>" % self.fields[myField].label)
                if self.fields[myField].widget.attrs.get('class') :
                    self.fields[myField].widget.attrs['class'] += ' form-control'
                else:
                    self.fields[myField].widget.attrs['class'] = 'form-control '



    class Meta(object):
        model = Video
        fields = '__all__'
        exclude = ['owner']
        widgets = {'date_added': widgets.AdminDateWidget,
                   'date_evt': widgets.AdminDateWidget,
                   }


class ChannelForm(forms.ModelForm):

    def __init__(self, *args, **kwargs):

        super(ChannelForm, self).__init__(*args, **kwargs)
        pickers = {'image': "img"}
        self.fields['headband'].widget = CustomFilePickerWidget(
            pickers=pickers)

    class Meta(object):
        model = Channel
        fields = '__all__'


class ThemeForm(forms.ModelForm):

    def __init__(self, *args, **kwargs):
        super(ThemeForm, self).__init__(*args, **kwargs)
        pickers = {'image': "img"}
        self.fields['headband'].widget = CustomFilePickerWidget(
            pickers=pickers)

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
