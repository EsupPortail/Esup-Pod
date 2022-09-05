from django.conf import settings
from django.db import IntegrityError
from django.http import HttpResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_protect
from django.contrib import messages
from django.shortcuts import get_object_or_404
from django.utils.translation import ugettext_lazy as _
from django.core.exceptions import PermissionDenied
from django.template.loader import render_to_string
from django.contrib.admin.views.decorators import staff_member_required
from django.core.exceptions import SuspiciousOperation
from django.db.models import Count, Q
from django.core.exceptions import ObjectDoesNotExist
from django.contrib.auth.models import User
from .models import UserFolder
from .models import CustomFileModel
from .models import CustomImageModel
from .forms import UserFolderForm
from .forms import CustomFileModelForm
from .forms import CustomImageModelForm
from pod.main.views import remove_accents
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseBadRequest
import re
import json
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger


IMAGE_ALLOWED_EXTENSIONS = getattr(
    settings,
    "IMAGE_ALLOWED_EXTENSIONS",
    (
        "jpg",
        "jpeg",
        "bmp",
        "png",
        "gif",
        "tiff",
    ),
)

FILE_ALLOWED_EXTENSIONS = getattr(
    settings,
    "FILE_ALLOWED_EXTENSIONS",
    (
        "doc",
        "docx",
        "odt",
        "pdf",
        "xls",
        "xlsx",
        "ods",
        "ppt",
        "pptx",
        "txt",
        "html",
        "htm",
        "vtt",
        "srt",
    ),
)

TEST_SETTINGS = getattr(settings, "TEST_SETTINGS", False)
FOLDER_FILE_TYPE = ["image", "file"]


@csrf_protect
@staff_member_required(redirect_field_name="referrer")
def home(request, type=None):
    if type is not None and type not in FOLDER_FILE_TYPE:
        raise SuspiciousOperation("--> Invalid type")
    user_home_folder = get_object_or_404(UserFolder, name="home", owner=request.user)
    share_folder = (
        UserFolder.objects.filter(access_groups=request.user.owner.accessgroup_set.all())
        .exclude(owner=request.user)
        .order_by("owner", "id")
    )

    share_folder_user = (
        UserFolder.objects.filter(users=request.user)
        .exclude(owner=request.user)
        .order_by("owner", "id")
    )
    current_session_folder = get_current_session_folder(request)

    template = "podfile/home_content.html" if (request.is_ajax()) else "podfile/home.html"

    return render(
        request,
        template,
        {
            "user_home_folder": user_home_folder,
            "user_folder": [],
            "share_folder": share_folder,
            "share_folder_user": share_folder_user,
            "current_session_folder": current_session_folder,
            "form_file": CustomFileModelForm(),
            "form_image": CustomImageModelForm(),
            "type": type,
            "page_title": _("My files"),
        },
    )


def get_current_session_folder(request):
    try:
        current_session_folder = UserFolder.objects.filter(
            Q(
                owner=request.user,
                name=request.session.get("current_session_folder", "home"),
            )
            | Q(
                users=request.user,
                name=request.session.get("current_session_folder", "home"),
            )
            | Q(
                access_groups__in=request.user.owner.accessgroup_set.all(),
                name=request.session.get("current_session_folder", "home"),
            )
        )
    except ObjectDoesNotExist:
        if request.user.is_superuser:
            try:
                current_session_folder = UserFolder.objects.filter(
                    name=request.session.get("current_session_folder", "home")
                )
                return current_session_folder
            except ObjectDoesNotExist:
                pass
        current_session_folder = UserFolder.objects.filter(
            owner=request.user, name="home"
        )
    return current_session_folder.first()


@csrf_protect
@staff_member_required(redirect_field_name="referrer")
def get_folder_files(request, id, type=None):
    if type is None:
        type = request.GET.get("type", None)
    folder = get_object_or_404(UserFolder, id=id)

    if (
        request.user != folder.owner
        and not (
            folder.access_groups.filter(
                code_name__in=[
                    name[0]
                    for name in request.user.owner.accessgroup_set.values_list(
                        "code_name"
                    )
                ]
            ).exists()
        )
        and not (
            request.user.is_superuser
            or request.user.has_perm("podfile.change_userfolder")
        )
        and not (request.user in folder.users.all())
    ):
        messages.add_message(request, messages.ERROR, _("You cannot see this folder."))
        raise PermissionDenied

    request.session["current_session_folder"] = folder.name

    rendered = render_to_string(
        "podfile/list_folder_files.html",
        {
            "folder": folder,
            "type": type,
        },
        request,
    )

    list_element = {"list_element": rendered, "folder_id": folder.id}
    data = json.dumps(list_element)
    return HttpResponse(data, content_type="application/json")


def get_rendered(request):
    user_home_folder = get_object_or_404(UserFolder, name="home", owner=request.user)

    user_folder = UserFolder.objects.filter(owner=request.user).exclude(
        owner=request.user, name="home"
    )

    share_folder = (
        UserFolder.objects.filter(
            access_groups__in=request.user.owner.accessgroup_set.all()
        )
        .exclude(owner=request.user)
        .order_by("owner", "id")
    )

    share_folder_user = (
        UserFolder.objects.filter(users=request.user)
        .exclude(owner=request.user)
        .order_by("owner", "id")
    )

    current_session_folder = get_current_session_folder(request)

    rendered = render_to_string(
        "podfile/userfolder.html",
        {
            "user_home_folder": user_home_folder,
            "user_folder": user_folder,
            "share_folder": share_folder,
            "share_folder_user": share_folder_user,
            "current_session_folder": current_session_folder,
        },
        request,
    )
    return rendered, current_session_folder


def decide_owner(request, form, folder):
    if hasattr(form.instance, "owner"):
        return form.instance.owner
    else:
        return request.user


@csrf_protect
@staff_member_required(redirect_field_name="referrer")
def editfolder(request):
    new_folder = False

    form = UserFolderForm(request.POST)
    if request.POST.get("folderid") and request.POST.get("folderid") != "":
        folder = get_object_or_404(UserFolder, id=request.POST["folderid"])
        if folder.name == "home" or (
            request.user != folder.owner
            and not (
                request.user.is_superuser
                or request.user.has_perm("podfile.change_userfolder")
                or (request.user in folder.users.all())
            )
        ):
            messages.add_message(
                request, messages.ERROR, _("You cannot edit this folder.")
            )
            raise PermissionDenied
        form = UserFolderForm(request.POST, instance=folder)

    if form.is_valid():
        folder = form.save(commit=False)
        folder.owner = decide_owner(request, form, folder)

        try:
            if not request.POST.get("folderid"):
                new_folder = True
            folder.save()
        except IntegrityError:
            messages.add_message(
                request,
                messages.ERROR,
                _("Two folders cannot have the same name."),
            )
            raise PermissionDenied

        request.session["current_session_folder"] = folder.name

    rendered, current_session_folder = get_rendered(request)

    list_element = {
        "list_element": rendered,
        "folder_id": current_session_folder.id,
        "folder_name": current_session_folder.name,
        "new_folder": new_folder,
    }
    data = json.dumps(list_element)

    return HttpResponse(data, content_type="application/json")


@csrf_protect
@staff_member_required(redirect_field_name="referrer")
def deletefolder(request):
    if request.POST["id"]:
        folder = get_object_or_404(UserFolder, id=request.POST["id"])
        if folder.name == "home" or (
            request.user != folder.owner
            and not (
                request.user.is_superuser
                or request.user.has_perm("podfile.delete_userfolder")
            )
        ):
            messages.add_message(
                request, messages.ERROR, _("You cannot delete home folder.")
            )
            raise PermissionDenied
        else:
            folder.delete()

    rendered, current_session_folder = get_rendered(request)

    list_element = {
        "list_element": rendered,
        "folder_id": current_session_folder.id,
        "deleted": True,
        "deleted_id": request.POST["id"],
    }
    data = json.dumps(list_element)
    return HttpResponse(data, content_type="application/json")


@csrf_protect
@staff_member_required(redirect_field_name="referrer")
def deletefile(request):
    if request.POST["id"] and request.POST["classname"]:
        file = get_object_or_404(eval(request.POST["classname"]), id=request.POST["id"])
        folder = file.folder
        if request.user != file.created_by and not (
            request.user.is_superuser
            or request.user.has_perm("podfile.delete_customfilemodel")
            or request.user.has_perm("podfile.delete_customimagemodel")
            or (request.user in folder.users.all())
        ):
            messages.add_message(
                request, messages.ERROR, _("You cannot delete this file.")
            )
            raise PermissionDenied
        else:
            file.delete()

        rendered = render_to_string(
            "podfile/list_folder_files.html",
            {
                "folder": folder,
            },
            request,
        )

        list_element = {"list_element": rendered, "folder_id": folder.id}
        data = json.dumps(list_element)
        return HttpResponse(data, content_type="application/json")
    else:
        raise SuspiciousOperation("You must send data in post")


@csrf_protect
@staff_member_required(redirect_field_name="referrer")
def uploadfiles(request):

    if request.POST.get("folderid") and request.POST.get("folderid") != "":
        folder = get_object_or_404(UserFolder, id=request.POST["folderid"])
        if request.user != folder.owner and not (
            request.user.is_superuser
            or request.user.has_perm("podfile.add_customfilemodel")
            or request.user.has_perm("podfile.add_customimagemodel")
            or (request.user in folder.users.all())
        ):
            messages.add_message(
                request,
                messages.ERROR,
                _("You cannot edit file on this folder."),
            )
            raise PermissionDenied
        else:
            upload_errors = ""
            if request.FILES:
                files = request.FILES.getlist("ufile")
                upload_errors = save_uploaded_files(request, folder, files)
            if request.POST.get("type"):
                rendered = render_to_string(
                    "podfile/list_folder_files.html",
                    {"folder": folder, "type": request.POST["type"]},
                    request,
                )
            else:
                rendered = render_to_string(
                    "podfile/list_folder_files.html",
                    {
                        "folder": folder,
                    },
                    request,
                )
            list_element = {
                "list_element": rendered,
                "folder_id": folder.id,
                "upload_errors": upload_errors,
            }

            data = json.dumps(list_element)

            return HttpResponse(data, content_type="application/json")
    else:
        raise SuspiciousOperation("You must send data in post")


def save_uploaded_files(request, folder, files):
    upload_errors = ""
    for file in files:
        # Check if file is image
        fname, dot, extension = file.name.rpartition(".")
        if "image" in file.content_type and extension in IMAGE_ALLOWED_EXTENSIONS:
            form_file = CustomImageModelForm({"folder": folder.id}, {"file": file})
            upload_errors = manage_form_file(request, upload_errors, fname, form_file)
        elif extension in FILE_ALLOWED_EXTENSIONS:
            form_file = CustomFileModelForm({"folder": folder.id}, {"file": file})
            upload_errors = manage_form_file(request, upload_errors, fname, form_file)
        else:
            upload_errors += "\n%s" % _(
                "The file %(fname)s has not allowed format" % {"fname": fname}
            )
    return upload_errors


def manage_form_file(request, upload_errors, fname, form_file):
    if form_file.is_valid():
        file = form_file.save(commit=False)
        if hasattr(form_file.instance, "created_by"):
            file.created_by = form_file.instance.created_by
        else:
            file.created_by = request.user
        file.save()
    else:
        upload_errors += "\n%s" % _(
            "The file %(fname)s is not valid (%(form_error)s)"
            % {"fname": fname, "form_error": form_file.errors.as_json()}
        )

    return upload_errors


@csrf_protect
@staff_member_required(redirect_field_name="referrer")
def changefile(request):
    # did it only for flake !
    file = CustomFileModel()
    file = CustomImageModel()

    if request.POST and request.is_ajax():
        folder = get_object_or_404(UserFolder, id=request.POST["folder"])
        if request.user != folder.owner and not (
            request.user.is_superuser
            or request.user.has_perm("podfile.change_customfilemodel")
            or request.user.has_perm("podfile.change_customimagemodel")
            or (request.user in folder.users.all())
        ):
            messages.add_message(
                request, messages.ERROR, _("You cannot access this folder.")
            )
            raise PermissionDenied

        file = get_object_or_404(
            eval(request.POST["file_type"]), id=request.POST["file_id"]
        )
        if request.user != file.created_by and not (
            request.user.is_superuser
            or request.user.has_perm("podfile.change_customfilemodel")
            or request.user.has_perm("podfile.change_customimagemodel")
            or (request.user in folder.users.all())
        ):
            messages.add_message(request, messages.ERROR, _("You cannot edit this file."))
            raise PermissionDenied

        form_file = eval("%sForm" % request.POST["file_type"])(
            request.POST, request.FILES, instance=file
        )

        if form_file.is_valid():
            if form_file.cleaned_data["folder"] != folder:
                raise SuspiciousOperation("Folder must be the same")
            file = form_file.save(commit=False)
            if hasattr(form_file.instance, "created_by"):
                file.created_by = form_file.instance.created_by
            else:
                file.created_by = request.user
            file.save()

            rendered = render_to_string(
                "podfile/list_folder_files.html",
                {
                    "folder": folder,
                },
                request,
            )

            list_element = {"list_element": rendered, "folder_id": folder.id}
            data = json.dumps(list_element)

            return HttpResponse(data, content_type="application/json")
        else:
            some_data_to_dump = {
                "errors": "%s" % _("Please correct errors"),
                "form_error": form_file.errors.as_json(),
            }
            data = json.dumps(some_data_to_dump)
            return HttpResponse(data, content_type="application/json")
    else:
        raise SuspiciousOperation("You must send data in post")

    some_data_to_dump = {"status": "error", "response": ""}
    data = json.dumps(some_data_to_dump)

    return HttpResponse(data, content_type="application/json")


# keep it for completion part....
def file_edit_save(request, folder):
    print(request.FILES)
    form_file = None
    if request.POST.get("file_id") and request.POST.get("file_id") != "None":
        customfile = get_object_or_404(CustomFileModel, id=request.POST["file_id"])
        form_file = CustomFileModelForm(request.POST, request.FILES, instance=customfile)
    else:
        form_file = CustomFileModelForm(request.POST, request.FILES)
    if form_file.is_valid():
        if form_file.cleaned_data["folder"] != folder:
            raise SuspiciousOperation("Folder must be the same")
        customfile = form_file.save(commit=False)
        if hasattr(form_file.instance, "created_by"):
            customfile.created_by = form_file.instance.created_by
        else:
            customfile.created_by = request.user
        customfile.save()
        rendered = render_to_string(
            "podfile/list_folder_files.html",
            {
                "folder": folder,
            },
            request,
        )

        list_element = {
            "list_element": rendered,
            "folder_id": folder.id,
            "file_id": customfile.id,
        }
        data = json.dumps(list_element)
        return HttpResponse(data, content_type="application/json")
    else:
        some_data_to_dump = {
            "errors": "%s" % _("Please correct errors"),
            "form_error": form_file.errors.as_json(),
        }
        data = json.dumps(some_data_to_dump)
        return HttpResponse(data, content_type="application/json")


@csrf_protect
@staff_member_required(redirect_field_name="referrer")
def get_file(request, type):
    id = None
    if request.method == "POST" and request.POST.get("src"):
        id = request.POST.get("src")
    elif request.method == "GET" and request.GET.get("src"):
        id = request.GET.get("src")
    if type == "image":
        reqfile = get_object_or_404(CustomImageModel, id=id)
    else:
        reqfile = get_object_or_404(CustomFileModel, id=id)
    if (
        request.user != reqfile.folder.owner
        and not reqfile.folder.access_groups.filter(
            code_name__in=[
                name[0]
                for name in request.user.owner.accessgroup_set.values_list("code_name")
            ]
        ).exists()
        and not (
            request.user.is_superuser
            or request.user.has_perm("podfile.change_customfilemodel")
            or request.user.has_perm("podfile.change_customimagemodel")
            or (request.user in reqfile.folder.users.all())
        )
    ):
        messages.add_message(request, messages.ERROR, _("You cannot see this folder."))
        raise PermissionDenied

    request.session["current_session_folder"] = reqfile.folder.name
    file_p = reqfile.file.__str__()
    reg = re.compile(r"[\w\d_\-]+(\.[a-z]{1,4})$")
    file_name = re.search(reg, file_p).group()
    try:
        with open(reqfile.file.path, "r") as f:
            fc = f.read()
            some_data_to_dump = {
                "status": "success",
                "file_name": file_name,
                "id_file": reqfile.id,
                "id_folder": reqfile.folder.id,
                "response": fc,
            }
    except OSError:
        some_data_to_dump = {"status": "error", "response": ""}
    data = json.dumps(some_data_to_dump)
    return HttpResponse(data, content_type="application/json")


@login_required(redirect_field_name="referrer")
def folder_shared_with(request):
    if request.is_ajax():
        foldid = request.GET.get("foldid", 0)
        if foldid == 0:
            return HttpResponseBadRequest()
        folder = UserFolder.objects.get(id=foldid)
        if folder.owner == request.user or request.user.is_superuser:
            data = json.dumps(
                list(folder.users.values("id", "first_name", "last_name", "username"))
            )
            mimetype = "application/json"
            return HttpResponse(data, mimetype)
        else:
            return HttpResponseBadRequest()
    else:
        return HttpResponseBadRequest()


@login_required(redirect_field_name="referrer")
def user_share_autocomplete(request):
    if request.is_ajax():
        foldid = request.GET.get("foldid", 0)
        if foldid == 0:
            return HttpResponseBadRequest()
        folder = UserFolder.objects.get(id=foldid)
        shared_users = folder.users.all()
        owner = folder.owner

        VALUES_LIST = ["id", "username", "first_name", "last_name"]
        q = remove_accents(request.GET.get("term", "").lower())
        users = (
            User.objects.filter(
                Q(username__istartswith=q)
                | Q(last_name__istartswith=q)
                | Q(first_name__istartswith=q)
            )
            .exclude(pk__in=shared_users)
            .exclude(id=owner.id)
            .distinct()
            .order_by("last_name")
            .values(*list(VALUES_LIST))
        )

        data = json.dumps(list(users))
    else:
        return HttpResponseBadRequest()
    mimetype = "application/json"
    return HttpResponse(data, mimetype)


@login_required(redirect_field_name="referrer")
def remove_shared_user(request):
    if request.is_ajax():
        foldid = request.GET.get("foldid", 0)
        userid = request.GET.get("userid", 0)
        if foldid == 0 or userid == 0:
            return HttpResponseBadRequest()
        folder = UserFolder.objects.get(id=foldid)
        user = User.objects.get(id=userid)
        if folder.owner == request.user or request.user.is_superuser:
            folder.users.remove(user)
            folder.save()
            return HttpResponse(status=201)
        else:
            return HttpResponseBadRequest()
    else:
        return HttpResponseBadRequest()


@login_required(redirect_field_name="referrer")
def add_shared_user(request):
    if request.is_ajax():
        foldid = request.GET.get("foldid", 0)
        userid = request.GET.get("userid", 0)
        if foldid == 0 or userid == 0:
            return HttpResponseBadRequest()
        folder = UserFolder.objects.get(id=foldid)
        user = User.objects.get(id=userid)
        if folder.owner == request.user or request.user.is_superuser:
            folder.users.add(user)
            folder.save()
            return HttpResponse(status=201)
        else:
            return HttpResponseBadRequest()
    else:
        return HttpResponseBadRequest()


@login_required(redirect_field_name="referrer")
def get_current_session_folder_ajax(request):
    fold = request.session.get("current_session_folder", "home")
    mimetype = "application/json"
    return HttpResponse(json.dumps({"folder": fold}), mimetype)


def fetch_owners(request, folders_list):
    if request.user.is_superuser:
        for fold in folders_list:
            if fold["owner"] != request.user.id:
                fold["owner"] = User.objects.get(id=fold["owner"]).username
            else:
                del fold["owner"]
    return folders_list


def filter_folders_with_truly_files(folders):
    if not TEST_SETTINGS:
        return (
            folders.annotate(nbr_image=Count("customimagemodel", distinct=True))
            .annotate(nbr_file=Count("customfilemodel", distinct=True))
            .filter(Q(nbr_image__gt=0) | Q(nbr_file__gt=0))
        )
    return folders


@staff_member_required(redirect_field_name="referrer")
def user_folders(request):
    VALUES_LIST = ["id", "name"]
    if request.user.is_superuser:
        VALUES_LIST.append("owner")

    user_folder = UserFolder.objects.exclude(owner=request.user, name="home")

    if not request.user.is_superuser:
        user_folder = user_folder.filter(owner=request.user)

    # filter folders to keep only those that have files
    user_folder = filter_folders_with_truly_files(user_folder)

    user_folder = user_folder.values(*VALUES_LIST)

    search = request.GET.get("search", "")
    current_fold = json.loads(
        get_current_session_folder_ajax(request).content.decode("utf-8")
    )["folder"]
    if search != "":
        user_folder = user_folder.filter(
            Q(name__icontains=search)
            | (Q(name=current_fold) & ~Q(owner=request.user, name="home"))
        )

    page = request.GET.get("page", 1)
    user_folder = user_folder.order_by("owner", "name")
    paginator = Paginator(user_folder, 10)
    try:
        folders = paginator.page(page)
    except PageNotAnInteger:
        folders = paginator.page(1)
    except EmptyPage:
        folders = paginator.page(paginator.num_pages)

    folders = fetch_owners(request, folders)
    folders = list(folders)
    json_resp = {
        "folders": folders,
        "current_page": int(page),
        "next_page": (-1 if ((int(page) + 1) > paginator.num_pages) else (int(page) + 1)),
        "total_pages": paginator.num_pages,
    }
    data = json.dumps(json_resp)
    mimetype = "application/json"
    return HttpResponse(data, mimetype)
