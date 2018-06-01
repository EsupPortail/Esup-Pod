from django import forms
from pod.authentication.models import Owner
from pod.filepicker.widgets import CustomFilePickerWidget
from django.apps import apps

FILEPICKER = True if apps.is_installed('pod.filepicker') else False

class OwnerAdminForm(forms.ModelForm):

    def __init__(self, *args, **kwargs):
        super(OwnerAdminForm, self).__init__(*args, **kwargs)
        if FILEPICKER:
            pickers = {'image': "img"}
            self.fields['userpicture'].widget = CustomFilePickerWidget(
                pickers=pickers)

    class Meta(object):
        model = Owner
        fields = '__all__'

class FrontOwnerForm(OwnerAdminForm):
    class Meta(object):
        model = Owner
        fields = ('userpicture',)