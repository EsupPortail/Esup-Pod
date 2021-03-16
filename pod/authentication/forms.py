from django import forms
from pod.authentication.models import Owner, GroupSite
from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.admin.widgets import FilteredSelectMultiple
from django.contrib.auth.models import Group
from django.utils.translation import ugettext_lazy as _
from django.contrib.sites.models import Site

FILEPICKER = False
if getattr(settings, 'USE_PODFILE', False):
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


class GroupSiteAdminForm(forms.ModelForm):

    def __init__(self, *args, **kwargs):
        super(GroupSiteAdminForm, self).__init__(*args, **kwargs)

    class Meta(object):
        model = GroupSite
        fields = '__all__'


class FrontOwnerForm(OwnerAdminForm):

    class Meta(object):
        model = Owner
        fields = ('userpicture',)


User = get_user_model()


# Create ModelForm based on the Group model.
class GroupAdminForm(forms.ModelForm):
    class Meta:
        model = Group
        exclude = []

    # Add the users field.
    users = forms.ModelMultipleChoiceField(
         queryset=User.objects.all(),
         required=False,
         # Use the pretty 'filter_horizontal widget'.
         widget=FilteredSelectMultiple(_('Users'), False),
         label=_('Users')
    )

    def __init__(self, *args, **kwargs):
        # Do the normal form initialisation.
        super(GroupAdminForm, self).__init__(*args, **kwargs)
        # If it is an existing group (saved objects have a pk).
        if self.instance.pk:
            # Populate the users field with the current Group users.
            self.fields['users'].initial = self.instance.user_set.all()
        self.fields['users'].queryset = self.fields['users'].queryset.filter(
                owner__sites=Site.objects.get_current())

    def save_m2m(self):
        # Add the users to the Group.
        self.instance.user_set.set(self.cleaned_data['users'])

    def save(self, *args, **kwargs):
        # Default save
        instance = super(GroupAdminForm, self).save()
        # Save many-to-many data
        self.save_m2m()
        return instance
