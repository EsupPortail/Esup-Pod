"""Esup-Pod podfile URL Configuration."""

from django.urls import path, re_path

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
    path("", home, name="home"),
    re_path(r"^(?P<type>[\-\d\w]+)$", home, name="home"),
    re_path(
        r"^get_folder_files/(?P<id>[\d]+)/$",
        get_folder_files,
        name="get_folder_files",
    ),
    re_path(
        r"^get_folder_files/(?P<id>[\d]+)/(?P<type>[\-\d\w]+)/$",
        get_folder_files,
        name="get_folder_files",
    ),
    re_path(r"^get_file/(?P<type>[\-\d\w]+)/$", get_file, name="get_file"),
    path("editfolder/", editfolder, name="editfolder"),
    path("deletefolder/", deletefolder, name="deletefolder"),
    path("deletefile/", deletefile, name="deletefile"),
    path("changefile/", changefile, name="changefile"),
    path("uploadfiles/", uploadfiles, name="uploadfiles"),
    re_path(r"^ajax_calls/search_share_user/", user_share_autocomplete),
    re_path(r"^ajax_calls/folder_shared_with/", folder_shared_with),
    re_path(r"^ajax_calls/remove_shared_user/", remove_shared_user),
    re_path(r"^ajax_calls/add_shared_user/", add_shared_user),
    re_path(r"^ajax_calls/user_folders/", user_folders),
    re_path(r"^ajax_calls/current_session_folder/", get_current_session_folder_ajax),
]
