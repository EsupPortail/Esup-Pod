from django import forms
from pod.filepicker.widgets import CustomFilePickerWidget
from pod.completion.models import Document


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
