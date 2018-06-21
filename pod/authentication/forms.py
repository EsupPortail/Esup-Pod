from django import forms
from pod.authentication.models import Owner
from django.apps import apps
if apps.is_installed('pod.podfile'):
    from pod.podfile.widgets import CustomFileWidget
    FILEPICKER = True


class OwnerAdminForm(forms.ModelForm):

    def __init__(self, *args, **kwargs):
        super(OwnerAdminForm, self).__init__(*args, **kwargs)
        if FILEPICKER:
            self.fields['userpicture'].widget = CustomFileWidget(
                type="image")

    class Meta(object):
        model = Owner
        fields = '__all__'


class FrontOwnerForm(OwnerAdminForm):

    class Meta(object):
        model = Owner
        fields = ('userpicture',)
