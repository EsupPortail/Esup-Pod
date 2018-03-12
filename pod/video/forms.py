from django import forms
from pod.filepicker.widgets import CustomFilePickerWidget
from pod.video.models import Video


class VideoForm(forms.ModelForm):

    def __init__(self, *args, **kwargs):
        super(VideoForm, self).__init__(*args, **kwargs)
        pickers = {'image': "img"}
        self.fields['thumbnail'].widget = CustomFilePickerWidget(
            pickers=pickers)
        self.fields['thumbnail'].disabled = True

    class Meta(object):
        model = Video
        fields = '__all__'
