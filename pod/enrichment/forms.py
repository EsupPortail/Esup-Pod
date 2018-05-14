from django import forms
from pod.filepicker.widgets import CustomFilePickerWidget
from pod.enrichment.models import Enrichment

class EnrichmentAdminForm(forms.ModelForm):

    def __init__(self, *args, **kwargs):
        super(EnrichmentAdminForm, self).__init__(*args, **kwargs)
        pickers = {'file': "file"}
        self.fields['document'].widget = CustomFilePickerWidget(
            pickers=pickers)
        pickers = {'image': "img"}
        self.fields['image'].widget = CustomFilePickerWidget(
        	pickers=pickers)

    class Meta(object):
        model = Enrichment
        fields = '__all__'