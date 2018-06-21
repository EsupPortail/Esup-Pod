"""
podfile URL Configuration
"""


from django.conf.urls import url

from .views import folder, editfile, editimage

urlpatterns = [
    url(r'^folder/(?P<type>[\-\d\w]+)/', folder, name='folder'),
    url(r'^editfile/(?P<id>[\d]+)/', editfile, name='editfile'),
    url(r'^editimage/(?P<id>[\d]+)/', editimage, name='editimage'),
]
