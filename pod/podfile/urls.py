"""
podfile URL Configuration
"""


from django.conf.urls import url

from .views import folder, editfile, editimage, get_files

app_name = 'podfile'
urlpatterns = [
    url(r'^folder/(?P<type>[\-\d\w]+)/$', folder, name='folder'),
    url(r'^folder/(?P<type>[\-\d\w]+)/(?P<id>[\d]+)/$', folder, name='folder'),
    url(
        r'^get_files/(?P<type>[\-\d\w]+)/(?P<id>[\d]+)/$',
        get_files,
        name='get_files'),
    url(r'^editfile/(?P<id>[\d]+)/$', editfile, name='editfile'),
    url(r'^editimage/(?P<id>[\d]+)/$', editimage, name='editimage'),
]
