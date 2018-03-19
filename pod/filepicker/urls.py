from django.conf.urls import url
from .file_pickers import delete

urlpatterns = [
    url(r'^delete/file/(?P<file>[\-\d\w]+)/(?P<ext>[\-\d\w]+)/$',
        delete, name='delete-files'),
]
