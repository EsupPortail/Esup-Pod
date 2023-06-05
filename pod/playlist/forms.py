from django import forms
from django.contrib.sites.models import Site
from django.utils.translation import ugettext_lazy as _


class PlaylistForm(forms.ModelForm):
    name = forms.CharField(label=_("Name"), max_length=100)
