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


from .models import UserFolder
from .models import CustomFileModel
from .models import CustomImageModel
from .forms import UserFolderForm
from .forms import CustomFileModelForm
from .forms import CustomImageModelForm

import json
from itertools import chain

FILE_ACTION = ['new', 'modify', 'delete', 'save']
FOLDER_FILE_TYPE = ['image', 'file']


@csrf_protect
@staff_member_required(redirect_field_name='referrer')
def folder(request, type, id=""):

    if type not in FOLDER_FILE_TYPE:
        raise SuspiciousOperation('Invalid type')

    if (request.POST.get("action")
            and request.POST.get("action") == "delete"):
        folder = get_object_or_404(
            UserFolder, id=request.POST['id'])
        folder.delete()

    # list_folder = UserFolder.objects.filter(owner=request.user)
    """
    list_folder = UserFolder.objects.filter(
        owner=request.user
    ) | UserFolder.objects.filter(
        groups__in=request.user.groups.all()
    )
    """
    user_folder = UserFolder.objects.filter(
        owner=request.user
    )
    group_user = UserFolder.objects.filter(
        groups__in=request.user.groups.all()
    ).order_by('owner', 'id')
    list_folder = list(chain(user_folder, group_user))

    form = UserFolderForm()
    """
    current_folder = get_object_or_404(
        UserFolder, id=request.POST['current_folder']) if (
        request.POST.get("current_folder")
        and request.POST.get("current_folder") != "") else (
        UserFolder.objects.get(owner=request.user, name="home")
    )
    """
    current_folder = get_object_or_404(
        UserFolder, id=id) if id != "" else (
        UserFolder.objects.get(owner=request.user, name="home"))

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
            folder.owner = request.user
            folder.save()
            current_folder = folder

    return render(request,
                  'podfile/list_folder.html',
                  {'list_folder': list_folder,
                   'form': form,
                   "current_folder": current_folder,
                   "type": type
                   })

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
            _(u'You cannot edit this folder.'))
        raise PermissionDenied

    if request.POST and request.is_ajax():
        if request.POST['action'] in FILE_ACTION:
            return eval(
                'image_edit_{0}(request, folder)'.format(
                    request.POST['action'])
            )


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
        "podfile/list_image.html",
        {'list_file': folder.customimagemodel_set.all(),
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
    form_image = None

    if (request.POST.get("file_id")
            and request.POST.get("file_id") != "None"):
        customImage = get_object_or_404(
            CustomImageModel, id=request.POST['file_id'])
        form_image = CustomImageModelForm(
            request.POST, request.FILES, instance=customImage)
    else:
        form_image = CustomImageModelForm(request.POST, request.FILES)

    if form_image.is_valid():
        customImage = form_image.save(commit=False)
        customImage.created_by = request.user
        customImage.save()
        rendered = render_to_string(
            "podfile/list_image.html",
            {'list_file': customImage.folder.customimagemodel_set.all(),
             'current_folder': folder
             }, request)
        list_element = {
            'list_element': rendered
        }
        data = json.dumps(list_element)
        return HttpResponse(data, content_type='application/json')
    else:
        rendered = render_to_string("podfile/form_image.html",
                                    {'form_image': form_image,
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
        if request.POST['action'] in FILE_ACTION:
            return eval(
                'file_edit_{0}(request, folder)'.format(
                    request.POST['action'])
            )


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
         'current_folder': folder
         }, request)
    list_element = {
        'list_element': rendered
    }
    data = json.dumps(list_element)
    return HttpResponse(data, content_type='application/json')


def file_edit_new(request, folder):
    form_file = CustomFileModelForm(initial={"folder": folder})
    return render(request, "podfile/form_file.html",
                  {'form_file': form_file, "folder": folder}
                  )


def file_edit_modify(request, folder):
    customfile = get_object_or_404(CustomFileModel, id=request.POST['id'])
    form_file = CustomFileModelForm(instance=customfile)
    return render(request, "podfile/form_file.html",
                  {'form_file': form_file,
                   "folder": folder
                   }
                  )


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
        customfile = form_file.save(commit=False)
        customfile.created_by = request.user
        customfile.save()
        rendered = render_to_string(
            "podfile/list_file.html",
            {'list_file': customfile.folder.customfilemodel_set.all(),
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
