from django import forms
from django.conf import settings

from pod.live.models import Building
from pod.live.models import Broadcaster

FILEPICKER = False
if getattr(settings, 'USE_PODFILE', False):
    FILEPICKER = True
    from pod.podfile.widgets import CustomFileWidget


class BuildingAdminForm(forms.ModelForm):
    required_css_class = 'required'
    is_staff = True
    is_superuser = False
    admin_form = True

    def __init__(self, *args, **kwargs):
        super(BuildingAdminForm, self).__init__(*args, **kwargs)
        if FILEPICKER:
            self.fields['headband'].widget = CustomFileWidget(type="image")
        #if not self.is_superuser:
         #   del self.fields['sites']

    def clean(self):
        super(BuildingAdminForm, self).clean()

    class Meta(object):
        model = Building
        fields = '__all__'


class BroadcasterAdminForm(forms.ModelForm):
    required_css_class = 'required'

    def __init__(self, *args, **kwargs):
        super(BroadcasterAdminForm, self).__init__(*args, **kwargs)
        if FILEPICKER:
            self.fields['poster'].widget = CustomFileWidget(type="image")

    def clean(self):
        super(BroadcasterAdminForm, self).clean()

    class Meta(object):
        model = Broadcaster
        fields = '__all__'
