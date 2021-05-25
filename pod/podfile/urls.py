"""
podfile URL Configuration
"""


from django.conf.urls import url

from .views import home, get_folder_files, get_file
from .views import editfolder, deletefolder
from .views import uploadfiles, deletefile, changefile
from .views import (
    folder_shared_with,
    user_share_autocomplete,
    user_folders,
    get_current_session_folder_ajax,
)
from .views import remove_shared_user, add_shared_user

app_name = "podfile"

urlpatterns = [
    url(r"^$", home, name="home"),
    url(r"^(?P<type>[\-\d\w]+)$", home, name="home"),
    url(
        r"^get_folder_files/(?P<id>[\d]+)/$",
        get_folder_files,
        name="get_folder_files",
    ),
    url(
        r"^get_folder_files/(?P<id>[\d]+)/(?P<type>[\-\d\w]+)/$",
        get_folder_files,
        name="get_folder_files",
    ),
    url(r"^get_file/(?P<type>[\-\d\w]+)/$", get_file, name="get_file"),
    url(r"^editfolder/$", editfolder, name="editfolder"),
    url(r"^deletefolder/$", deletefolder, name="deletefolder"),
    url(r"^deletefile/$", deletefile, name="deletefile"),
    url(r"^changefile/$", changefile, name="changefile"),
    url(r"^uploadfiles/$", uploadfiles, name="uploadfiles"),
    url(r"^ajax_calls/search_share_user/", user_share_autocomplete),
    url(r"^ajax_calls/folder_shared_with/", folder_shared_with),
    url(r"^ajax_calls/remove_shared_user/", remove_shared_user),
    url(r"^ajax_calls/add_shared_user/", add_shared_user),
    url(r"^ajax_calls/user_folders/", user_folders),
    url(r"^ajax_calls/current_session_folder/", get_current_session_folder_ajax),
]
