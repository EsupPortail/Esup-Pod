from django import forms
from django.utils.translation import ugettext_lazy as _
from django.utils.safestring import mark_safe
from pod.chapters.models import Chapter


class ChapterForm(forms.ModelForm):

    def __init__(self, *args, **kwargs):
        super(ChapterForm, self).__init__(*args, **kwargs)
        self.fields['video'].widget = forms.HiddenInput()
        self.fields['time'].widget.attrs['min'] = 0
        try:
            self.fields['time'].widget.attrs[
                'max'] = self.instance.video.duration - 1
        except Exception:
            self.fields['time'].widget.attrs['max'] = 36000
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
