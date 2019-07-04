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
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.core.exceptions import ObjectDoesNotExist

from .models import UserFolder
from .models import CustomFileModel
from .models import CustomImageModel
from .forms import UserFolderForm
from .forms import CustomFileModelForm
from .forms import CustomImageModelForm
from .forms import CustomFileModelCaptionMakerForm

import json
from itertools import chain

FILE_ACTION = ['new', 'modify', 'delete', 'save']
FOLDER_FILE_TYPE = ['image', 'file']


def get_folders(request, page):
    user_folder = UserFolder.objects.filter(
        owner=request.user
    ).exclude(owner=request.user, name="home")
    group_user = UserFolder.objects.filter(
        groups__in=request.user.groups.all()
    ).exclude(owner=request.user).order_by('owner', 'id')
    list_folder = list(chain(user_folder, group_user))

    paginator = Paginator(list_folder, 12)
    try:
        folders = paginator.page(page)
    except PageNotAnInteger:
        folders = paginator.page(1)
    except EmptyPage:
        folders = paginator.page(paginator.num_pages)
    return folders


def edit_folder(request, current_folder):
    form = UserFolderForm(request.POST)
    if (request.POST.get("id_folder")
            and request.POST.get("id_folder") != ""):
        folder = get_object_or_404(
            UserFolder, id=request.POST['id_folder'])
        if folder.name == "home" or (
            request.user != folder.owner
            and not request.user.is_superuser
        ):
            messages.add_message(
                request, messages.ERROR,
                _(u'You cannot edit this folder.'))
            raise PermissionDenied
        form = UserFolderForm(request.POST, instance=folder)

    if form.is_valid():
        folder = form.save(commit=False)
        if hasattr(form.instance, 'owner'):
            folder.owner = form.instance.owner
        else:
            folder.owner = request.user
        folder.save()
        current_folder = folder
        request.session['current_session_folder'] = current_folder.name
    return form, current_folder


def get_current_session_folder(request):
    try:
        current_session_folder = UserFolder.objects.get(
            owner=request.user,
            name=request.session.get(
                'current_session_folder',
                "home")
        )
        return current_session_folder
    except ObjectDoesNotExist:
        current_session_folder = UserFolder.objects.get(
            owner=request.user,
            name="home"
        )
        return current_session_folder


def get_list_file(type, folder, page):
    files = folder.customimagemodel_set.all() if (
        type == "image") else folder.customfilemodel_set.all()

    paginator = Paginator(files, 12)
    try:
        list_file = paginator.page(page)
    except PageNotAnInteger:
        list_file = paginator.page(1)
    except EmptyPage:
        list_file = paginator.page(paginator.num_pages)

    return list_file


@csrf_protect
@staff_member_required(redirect_field_name='referrer')
def folder(request, type, id=""):

    if type not in FOLDER_FILE_TYPE:
        raise SuspiciousOperation('Invalid type')

    if (request.POST.get("action")
            and request.POST.get("action") == "delete"):
        folder = get_object_or_404(
            UserFolder, id=request.POST['id'])
        if (
                folder.name == 'home'
                or (request.user != folder.owner
                    and not request.user.is_superuser)
        ):
            messages.add_message(
                request, messages.ERROR,
                _(u'You cannot delete home folder.'))
            raise PermissionDenied
        else:
            folder.delete()

    page = request.GET.get('page', 1)
    full_path = request.get_full_path().replace(
        "?page=%s" % page, "").replace(
        "&page=%s" % page, "").replace(
        "&infinite=true", "") if page else ""
    form = UserFolderForm()

    user_home_folder = get_object_or_404(
        UserFolder, name="home", owner=request.user)

    folders = get_folders(request, page)
    current_session_folder = get_current_session_folder(request)

    current_folder = get_object_or_404(
        UserFolder, id=id) if id != "" else (
        current_session_folder)

    request.session['current_session_folder'] = current_folder.name

    if (request.user != current_folder.owner
            and not request.user.groups.filter(
                name__in=[
                    name[0]
                    for name in current_folder.groups.values_list('name')
                ]
            ).exists()
            and not request.user.is_superuser):
        messages.add_message(
            request, messages.ERROR,
            _(u'You cannot see this folder.'))
        raise PermissionDenied

    if (request.POST.get("name")
            and request.POST.get("name") != ""):
        form, current_folder = edit_folder(request, current_folder)
        folders = get_folders(request, page)

    if request.GET.get('infinite', False):
        return render(
            request, 'podfile/infinite_folders.html',
            {'list_folder': folders, "type": type, "full_path": full_path})

    list_file = current_folder.customimagemodel_set.all() if (
        type == "image") else current_folder.customfilemodel_set.all()

    return render(request,
                  'podfile/list_folder.html',
                  {'list_folder': folders,
                   'form': form,
                   "current_folder": current_folder,
                   "list_file": list_file,
                   "type": type,
                   "full_path": full_path,
                   "user_home_folder": user_home_folder
                   })


@csrf_protect
@staff_member_required(redirect_field_name='referrer')
def get_files(request, type, id):
    folder = get_object_or_404(UserFolder, id=id)
    if (request.user != folder.owner
            and not request.user.groups.filter(
                name__in=[
                    name[0]
                    for name in folder.groups.values_list('name')
                ]
            ).exists()
            and not request.user.is_superuser):
        messages.add_message(
            request, messages.ERROR,
            _(u'You cannot see this folder.'))
        raise PermissionDenied

    request.session['current_session_folder'] = folder.name

    list_file = folder.customimagemodel_set.all() if (
        type == "image") else folder.customfilemodel_set.all()

    template_name = 'podfile/list_file.html'
    return render(
        request, template_name,
        {'list_file': list_file,
         "type": type,
         "current_folder": folder,
         })


@csrf_protect
@staff_member_required(redirect_field_name='referrer')
def get_file(request, type, id):
    if type == "image":
        reqfile = get_object_or_404(CustomImageModel, id=id)
    else:
        reqfile = get_object_or_404(CustomFileModel, id=id)
    if (request.user != reqfile.folder.owner
            and not request.user.groups.filter(
                name__in=[
                    name[0]
                    for name in reqfile.folder.groups.values_list('name')
                ]
            ).exists()
            and not request.user.is_superuser):
        messages.add_message(
            request, messages.ERROR,
            _(u'You cannot see this folder.'))
        raise PermissionDenied

    request.session['current_session_folder'] = reqfile.folder.name
    try:
        with open(reqfile.file.path, 'r') as f:
            fc = f.read()
            some_data_to_dump = {
                'status': "success",
                'response': fc
            }
    except OSError:
        some_data_to_dump = {
                'status': "error",
                'response': ''
            }
    data = json.dumps(some_data_to_dump)
    return HttpResponse(data, content_type='application/json')


##########################################################
# IMAGE
##########################################################


@csrf_protect
@staff_member_required(redirect_field_name='referrer')
def editimage(request, id):
    folder = get_object_or_404(UserFolder, id=id)
    if (request.user != folder.owner
            and not request.user.is_superuser):
        messages.add_message(
            request, messages.ERROR,
            _(u'You cannot edit this image.'))
        raise PermissionDenied

    if request.POST and request.is_ajax():
        if request.POST['action'] in FILE_ACTION:
            return eval(
                'image_edit_{0}(request, folder)'.format(
                    request.POST['action'])
            )
        else:
            raise SuspiciousOperation('Invalid action')
    else:
        raise SuspiciousOperation('You must send data in post')


def image_edit_delete(request, folder):
    customimage = get_object_or_404(CustomImageModel, id=request.POST['id'])
    if (request.user != customimage.created_by
            and not request.user.is_superuser):
        messages.add_message(
            request, messages.ERROR,
            _(u'You cannot edit this file.'))
        raise PermissionDenied
    customimage.delete()
    rendered = render_to_string(
        "podfile/list_file.html",
        {'list_file': folder.customimagemodel_set.all(),
         "type": "image",
         'current_folder': folder
         }, request)
    list_element = {
        'list_element': rendered
    }
    data = json.dumps(list_element)
    return HttpResponse(data, content_type='application/json')


def image_edit_new(request, folder):
    form_image = CustomImageModelForm(initial={"folder": folder})
    return render(request, "podfile/form_image.html",
                  {'form_image': form_image, "folder": folder}
                  )


def image_edit_modify(request, folder):
    customImage = get_object_or_404(CustomImageModel, id=request.POST['id'])
    form_image = CustomImageModelForm(instance=customImage)
    return render(request, "podfile/form_image.html",
                  {'form_image': form_image,
                   "folder": folder
                   }
                  )


def image_edit_save(request, folder):
    form_file = None

    if (request.POST.get("file_id")
            and request.POST.get("file_id") != "None"):
        customImage = get_object_or_404(
            CustomImageModel, id=request.POST['file_id'])
        form_file = CustomImageModelForm(
            request.POST, request.FILES, instance=customImage)
    else:
        form_file = CustomImageModelForm(request.POST, request.FILES)

    if form_file.is_valid():
        if form_file.cleaned_data["folder"] != folder:
            raise SuspiciousOperation('Folder must be the same')
        customImage = form_file.save(commit=False)
        if hasattr(form_file.instance, 'created_by'):
            customImage.created_by = form_file.instance.created_by
        else:
            customImage.created_by = request.user
        customImage.save()
        rendered = render_to_string(
            "podfile/list_file.html",
            {'list_file': customImage.folder.customimagemodel_set.all(),
             "type": "image",
             'current_folder': folder
             }, request)
        list_element = {
            'list_element': rendered
        }
        data = json.dumps(list_element)
        return HttpResponse(data, content_type='application/json')
    else:
        rendered = render_to_string("podfile/form_file.html",
                                    {'form_file': form_file,
                                     "folder": folder
                                     }, request)
        some_data_to_dump = {
            'errors': "%s" % _('Please correct errors'),
            'form': rendered
        }
        data = json.dumps(some_data_to_dump)
    return HttpResponse(data, content_type='application/json')


##########################################################
# FILE
##########################################################


@csrf_protect
@staff_member_required(redirect_field_name='referrer')
def editfile(request, id):
    folder = get_object_or_404(UserFolder, id=id)
    if (request.user != folder.owner
            and not request.user.is_superuser):
        messages.add_message(
            request, messages.ERROR,
            _(u'You cannot edit this folder.'))
        raise PermissionDenied

    if request.POST and request.is_ajax():
        if request.POST.get('action') in FILE_ACTION:
            return eval(
                'file_edit_{0}(request, folder)'.format(
                    request.POST['action'])
            )
        else:
            raise SuspiciousOperation('Invalid action')
    else:
        raise SuspiciousOperation('You must send data in post')


def file_edit_delete(request, folder):
    customfile = get_object_or_404(CustomFileModel, id=request.POST['id'])
    if (request.user != customfile.created_by
            and not request.user.is_superuser):
        messages.add_message(
            request, messages.ERROR,
            _(u'You cannot edit this file.'))
        raise PermissionDenied
    customfile.delete()
    rendered = render_to_string(
        "podfile/list_file.html",
        {'list_file': folder.customfilemodel_set.all(),
         'type': "file",
         'current_folder': folder
         }, request)
    list_element = {
        'list_element': rendered
    }
    data = json.dumps(list_element)
    return HttpResponse(data, content_type='application/json')


def file_edit_new(request, folder):
    if request.POST.get('captionMaker'):
        form_file = CustomFileModelCaptionMakerForm(initial={"folder": folder})
    else:   
        form_file = CustomFileModelForm(initial={"folder": folder})
    return render(request, "podfile/form_file.html",
                  {'form_file': form_file, "folder": folder})


def file_edit_modify(request, folder):
    customfile = get_object_or_404(CustomFileModel, id=request.POST['id'])
    form_file = CustomFileModelForm(instance=customfile)
    if request.POST.get('captionMaker'):
        del form_file.fields['file']
    return render(request, "podfile/form_file.html",
                  {'form_file': form_file,
                   "folder": folder})


def file_edit_save(request, folder):
    form_file = None
    if (request.POST.get("file_id")
            and request.POST.get("file_id") != "None"):
        customfile = get_object_or_404(
            CustomFileModel, id=request.POST['file_id'])
        form_file = CustomFileModelForm(
            request.POST, request.FILES, instance=customfile)
    else:
        form_file = CustomFileModelForm(request.POST, request.FILES)
    if form_file.is_valid():
        if form_file.cleaned_data["folder"] != folder:
            raise SuspiciousOperation('Folder must be the same')
        customfile = form_file.save(commit=False)
        if hasattr(form_file.instance, 'created_by'):
            customfile.created_by = form_file.instance.created_by
        else:
            customfile.created_by = request.user
        customfile.save()
        rendered = render_to_string(
            "podfile/list_file.html",
            {'list_file': customfile.folder.customfilemodel_set.all(),
             "type": "file",
             'current_folder': folder
             }, request)
        list_element = {
            'list_element': rendered
        }
        data = json.dumps(list_element)
        return HttpResponse(data, content_type='application/json')
    else:
        if (request.POST.get('captionMaker') and request.POST.get("file_id")
                and request.POST.get("file_id") != "None"):
            del form_file['file']
        elif (request.POST.get('captionMaker') and
                    (request.POST.get("file_id") == "None"
                    or not request.POST.get("file_id"))):
            form_file = CustomFileModelCaptionMakerForm(
                request.POST, request.FILES)
        rendered = render_to_string("podfile/form_file.html",
                                    {'form_file': form_file,
                                     "folder": folder
                                     }, request)
        some_data_to_dump = {
            'errors': "%s" % _('Please correct errors'),
            'form': rendered
        }
        data = json.dumps(some_data_to_dump)
    return HttpResponse(data, content_type='application/json')
