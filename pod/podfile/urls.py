"""
podfile URL Configuration
"""


from django.conf.urls import url

from .views import home, get_folder_files, get_file
from .views import editfolder, deletefolder
from .views import uploadfiles, deletefile, changefile

app_name = 'podfile'

urlpatterns = [
    url(r'^$', home, name='home'),
    url(r'^(?P<type>[\-\d\w]+)$', home, name='home'),
    url(
        r'^get_folder_files/(?P<id>[\d]+)/$',
        get_folder_files,
        name='get_folder_files'),
    url(
        r'^get_folder_files/(?P<id>[\d]+)/(?P<type>[\-\d\w]+)/$',
        get_folder_files,
        name='get_folder_files'),
    url(
        r'^get_file/(?P<type>[\-\d\w]+)/$',
        get_file,
        name='get_file'),
    url(r'^editfolder/$', editfolder, name='editfolder'),
    url(r'^deletefolder/$', deletefolder, name='deletefolder'),
    url(r'^deletefile/$', deletefile, name='deletefile'),
    url(r'^changefile/$', changefile, name='changefile'),
    url(r'^uploadfiles/$', uploadfiles, name='uploadfiles'),
]
