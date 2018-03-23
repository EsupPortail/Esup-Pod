from django import forms
from django.forms.widgets import HiddenInput
from django.utils.safestring import mark_safe
from pod.filepicker.widgets import CustomFilePickerWidget
from pod.completion.models import Contributor
from pod.completion.models import Document
from pod.completion.models import Track
from pod.completion.models import Overlay


class ContributorForm(forms.ModelForm):

    def __init__(self, *args, **kwargs):
        super(ContributorForm, self).__init__(*args, **kwargs)
        for myField in self.fields:
            self.fields['video'].widget = HiddenInput()
            self.fields[myField].widget.attrs[
                'placeholder'] = self.fields[myField].label
            if self.fields[myField].required:
                self.fields[myField].widget.attrs['class'] = 'required'
                label_unicode = u'{0}'.format(self.fields[myField].label)
                self.fields[myField].label = mark_safe(
                    '{0} <span class="special_class">*</span>'.format(
                        label_unicode))

    class Meta(object):
        model = Contributor
        fields = '__all__'


class DocumentForm(forms.ModelForm):

    def __init__(self, *args, **kwargs):
        super(DocumentForm, self).__init__(*args, **kwargs)
        for myField in self.fields:
            self.fields['video'].widget = HiddenInput()
            self.fields[myField].widget.attrs[
                'placeholder'] = self.fields[myField].label
            if self.fields[myField].required:
                self.fields[myField].widget.attrs['class'] = 'required'
                label_unicode = '{0}'.format(self.fields[myField].label)
                self.fields[myField].label = mark_safe(
                    '{0} <span class="special_class">*</span>'.format(
                        label_unicode))
        pickers = {'file': "file"}
        self.fields['document'].widget = CustomFilePickerWidget(
            pickers=pickers)

    class Meta(object):
        model = Document
        fields = '__all__'


class DocumentAdminForm(forms.ModelForm):

    def __init__(self, *args, **kwargs):
        super(DocumentAdminForm, self).__init__(*args, **kwargs)
        pickers = {'file': "file"}
        self.fields['document'].widget = CustomFilePickerWidget(
            pickers=pickers)

    class Meta(object):
        model = Document
        fields = '__all__'


class TrackForm(forms.ModelForm):

    def __init__(self, *args, **kwargs):
        super(TrackForm, self).__init__(*args, **kwargs)
        for myField in self.fields:
            self.fields['video'].widget = HiddenInput()
            self.fields[myField].widget.attrs[
                'placeholder'] = self.fields[myField].label
            if self.fields[myField].required or myField == 'src':
                self.fields[myField].widget.attrs['class'] = 'required'
                label_unicode = u'{0}'.format(self.fields[myField].label)
                self.fields[myField].label = mark_safe(
                    '{0} <span class="special_class">*</span>'.format(
                        label_unicode))
        pickers = {'file': "file"}
        self.fields['src'].widget = CustomFilePickerWidget(
            pickers=pickers)

    class Meta(object):
        model = Track
        fields = '__all__'


class TrackAdminForm(forms.ModelForm):

    def __init__(self, *args, **kwargs):
        super(TrackAdminForm, self).__init__(*args, **kwargs)
        pickers = {'file': "file"}
        self.fields['src'].widget = CustomFilePickerWidget(
            pickers=pickers)

    class Meta(object):
        model = Track
        fields = '__all__'


class OverlayForm(forms.ModelForm):

    def __init__(self, *args, **kwargs):
        super(OverlayForm, self).__init__(*args, **kwargs)
        self.fields['video'].widget = HiddenInput()
        self.fields['time_start'].widget.attrs['min'] = 1
        self.fields['time_end'].widget.attrs['min'] = 2
        try:
            self.fields['time_start'].widget.attrs[
                'max'] = self.instance.video.duration
            self.fields['time_end'].widget.attrs[
                'max'] = self.instance.video.duration
        except Exception:
            self.fields['time_start'].widget.attrs['max'] = 36000
            self.fields['time_end'].widget.attrs['max'] = 36000
        for myField in self.fields:
            self.fields[myField].widget.attrs[
                'placeholder'] = self.fields[myField].label
            if self.fields[myField].required:
                self.fields[myField].widget.attrs['class'] = 'required'
                label_unicode = u'{0}'.format(self.fields[myField].label)
                self.fields[myField].label = mark_safe(
                    '{0} <span class="special_class">*</span>'.format(
                        label_unicode))

    class Meta(object):
        model = Overlay
        fields = '__all__'
