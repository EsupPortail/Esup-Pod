from django import forms
from pod.filepicker.widgets import CustomFilePickerWidget
from pod.video.models import Video
from pod.video.models import Channel
from pod.video.models import Theme
from pod.video.models import Type
from pod.video.models import Discipline


class VideoForm(forms.ModelForm):

    def __init__(self, *args, **kwargs):
        super(VideoForm, self).__init__(*args, **kwargs)
        pickers = {'image': "img"}
        self.fields['thumbnail'].widget = CustomFilePickerWidget(
            pickers=pickers)

    class Meta(object):
        model = Video
        fields = '__all__'

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