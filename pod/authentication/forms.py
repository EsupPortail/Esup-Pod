from django import forms
from django.contrib.admin import widgets
from pod.authentication.models import Owner
from pod.filepicker.widgets import CustomFilePickerWidget

class OwnerAdminForm(forms.ModelForm):

    def __init__(self, *args, **kwargs):
        super(OwnerAdminForm, self).__init__(*args, **kwargs)
        pickers = {'image': "img"}
        self.fields['userpicture'].widget = CustomFilePickerWidget(
            pickers=pickers)

    class Meta(object):
        model = Owner
        fields = '__all__'