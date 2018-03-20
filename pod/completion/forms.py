from django import forms
from pod.filepicker.widgets import CustomFilePickerWidget
from pod.completion.models import Document
from pod.completion.models import Track


class DocumentForm(forms.ModelForm):

    def __init__(self, *args, **kwargs):
        super(DocumentForm, self).__init__(*args, **kwargs)
        pickers = {'file': "file"}
        self.fields['document'].widget = CustomFilePickerWidget(
            pickers=pickers)
        self.fields['document'].disabled = True

    class Meta(object):
        model = Document
        fields = '__all__'

class TrackForm(forms.ModelForm):

	def __init__(self, *args, **kwargs):
		super(TrackForm, self).__init__(*args, **kwargs)
		pickers = {'file': "file"}
		self.fields['src'].widget = CustomFilePickerWidget(
			pickers=pickers)
		self.fields['src'].disabled = True

	class Meta(object):
		model = Track
		fields = '__all__'