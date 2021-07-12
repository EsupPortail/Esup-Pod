from django import forms
from django.contrib.admin import widgets
from django.utils.translation import ugettext_lazy as _
from .models import InteractiveGroup
from django.contrib.auth.models import Group


class InteractiveGroupForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super(InteractiveGroupForm, self).__init__(*args, **kwargs)
        self.fields["groups"].widget = widgets.FilteredSelectMultiple(
            _("Groups"), False, attrs={}
        )
        self.fields["groups"].queryset = Group.objects.all()

    class Meta(object):
        model = InteractiveGroup
        fields = ("groups",)  # '__all__'
