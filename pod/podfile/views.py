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

from django.core.exceptions import ObjectDoesNotExist

from .models import UserFolder
from .models import CustomFileModel
from .models import CustomImageModel
from .forms import UserFolderForm
from .forms import CustomFileModelForm
from .forms import CustomImageModelForm

import json

IMAGE_ALLOWED_EXTENSIONS = getattr(
    settings, 'IMAGE_ALLOWED_EXTENSIONS', (
        'jpg',
        'jpeg',
        'bmp',
        'png',
        'gif',
        'tiff',
    )
)

FILE_ALLOWED_EXTENSIONS = getattr(
    settings, 'FILE_ALLOWED_EXTENSIONS', (
        'doc',
        'docx',
        'odt',
        'pdf',
        'xls',
        'xlsx',
        'ods',
        'ppt',
        'pptx',
        'txt',
        'html',
        'htm',
        'vtt',
        'srt',
    )
)
FOLDER_FILE_TYPE = ['image', 'file']


@csrf_protect
@staff_member_required(redirect_field_name='referrer')
def home(request, type=None):
    if type is not None and type not in FOLDER_FILE_TYPE:
        raise SuspiciousOperation('--> Invalid type')
    user_home_folder = get_object_or_404(
        UserFolder, name="home", owner=request.user)

    user_folder = UserFolder.objects.filter(
        owner=request.user
    ).exclude(owner=request.user, name="home")

    share_folder = UserFolder.objects.filter(
        groups__in=request.user.groups.all()
    ).exclude(owner=request.user).order_by('owner', 'id')

    current_session_folder = get_current_session_folder(request)

    template = 'podfile/home_content.html' if (
        request.is_ajax()) else 'podfile/home.html'

    return render(request,
                  template,
                  {
                      'user_home_folder': user_home_folder,
                      'user_folder': user_folder,
                      'share_folder': share_folder,
                      'current_session_folder': current_session_folder,
                      'form_file': CustomFileModelForm(),
                      'form_image': CustomImageModelForm(),
                      'type': type
                  }
                  )


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


@csrf_protect
@staff_member_required(redirect_field_name='referrer')
def get_folder_files(request, id, type=None):
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

    rendered = render_to_string(
        "podfile/list_folder_files.html",
        {'folder': folder,
         'type': type,
         }, request)

    list_element = {
        'list_element': rendered,
        'folder_id': folder.id
    }
    data = json.dumps(list_element)
    return HttpResponse(data, content_type='application/json')


def get_rendered(request):
    user_home_folder = get_object_or_404(
        UserFolder, name="home", owner=request.user)

    user_folder = UserFolder.objects.filter(
        owner=request.user
    ).exclude(owner=request.user, name="home")

    share_folder = UserFolder.objects.filter(
        groups__in=request.user.groups.all()
    ).exclude(owner=request.user).order_by('owner', 'id')

    current_session_folder = get_current_session_folder(request)

    rendered = render_to_string(
        'podfile/userfolder.html',
        {
            'user_home_folder': user_home_folder,
            'user_folder': user_folder,
            'share_folder': share_folder,
            'current_session_folder': current_session_folder,
        }, request)
    return rendered, current_session_folder


@csrf_protect
@staff_member_required(redirect_field_name='referrer')
def editfolder(request):

    form = UserFolderForm(request.POST)
    if (request.POST.get("folderid")
            and request.POST.get("folderid") != ""):
        folder = get_object_or_404(
            UserFolder, id=request.POST['folderid'])
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
        try:
            folder.save()
        except IntegrityError:
            messages.add_message(
                request, messages.ERROR,
                _(u'Two folders cannot have the same name.'))
            raise PermissionDenied

        request.session['current_session_folder'] = folder.name

    rendered, current_session_folder = get_rendered(request)

    list_element = {
        'list_element': rendered,
        'folder_id': current_session_folder.id
    }
    data = json.dumps(list_element)
    return HttpResponse(data, content_type='application/json')


@csrf_protect
@staff_member_required(redirect_field_name='referrer')
def deletefolder(request):
    if (request.POST['id']):
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

    rendered, current_session_folder = get_rendered(request)

    list_element = {
        'list_element': rendered,
        'folder_id': current_session_folder.id
    }
    data = json.dumps(list_element)
    return HttpResponse(data, content_type='application/json')


@csrf_protect
@staff_member_required(redirect_field_name='referrer')
def deletefile(request):
    if (request.POST['id'] and request.POST['classname']):
        file = get_object_or_404(
            eval(request.POST['classname']), id=request.POST['id'])
        folder = file.folder
        if (request.user != file.created_by
                and not request.user.is_superuser):
            messages.add_message(
                request, messages.ERROR,
                _(u'You cannot delete this file.'))
            raise PermissionDenied
        else:
            file.delete()

        rendered = render_to_string(
            "podfile/list_folder_files.html",
            {'folder': folder,
             }, request)

        list_element = {
            'list_element': rendered,
            'folder_id': folder.id
        }
        data = json.dumps(list_element)
        return HttpResponse(data, content_type='application/json')
    else:
        raise SuspiciousOperation('You must send data in post')


@csrf_protect
@staff_member_required(redirect_field_name='referrer')
def uploadfiles(request):

    if (request.POST.get("folderid")
            and request.POST.get("folderid") != ""):
        folder = get_object_or_404(
            UserFolder, id=request.POST['folderid'])
        if (
            request.user != folder.owner
            and not request.user.is_superuser
        ):
            messages.add_message(
                request, messages.ERROR,
                _(u'You cannot edit file on this folder.'))
            raise PermissionDenied
        else:
            upload_errors = ""
            if request.FILES:
                files = request.FILES.getlist('ufile')
                upload_errors = save_uploaded_files(request, folder, files)
            if request.POST.get("type"):
                rendered = render_to_string(
                    "podfile/list_folder_files.html",
                    {'folder': folder,
                     'type': request.POST['type']
                     }, request)
            else:
                rendered = render_to_string(
                    "podfile/list_folder_files.html",
                    {'folder': folder,
                     }, request)
            list_element = {
                'list_element': rendered,
                'folder_id': folder.id,
                'upload_errors': upload_errors
            }

            data = json.dumps(list_element)

            return HttpResponse(data, content_type='application/json')
    else:
        raise SuspiciousOperation('You must send data in post')


def save_uploaded_files(request, folder, files):
    upload_errors = ""
    for file in files:
        # Check if file is image
        fname, dot, extension = file.name.rpartition('.')
        if(
            "image" in file.content_type
            and extension in IMAGE_ALLOWED_EXTENSIONS
        ):
            form_file = CustomImageModelForm(
                {'folder': folder.id}, {'file': file})
            upload_errors = manage_form_file(
                request, upload_errors, fname, form_file)
        elif(extension in FILE_ALLOWED_EXTENSIONS):
            form_file = CustomFileModelForm(
                {'folder': folder.id}, {'file': file})
            upload_errors = manage_form_file(
                request, upload_errors, fname, form_file)
        else:
            upload_errors += "\n%s" % _(
                'The file %(fname)s has not allowed format' % {
                    'fname': fname
                }
            )
    return upload_errors


def manage_form_file(request, upload_errors, fname, form_file):
    if form_file.is_valid():
        file = form_file.save(commit=False)
        if hasattr(form_file.instance, 'created_by'):
            file.created_by = form_file.instance.created_by
        else:
            file.created_by = request.user
        file.save()
    else:
        upload_errors += "\n%s" % _(
            'The file %(fname)s is not valid (%(form_error)s)' % {
                'fname': fname,
                'form_error': form_file.errors.as_json()
            }
        )

    return upload_errors


@csrf_protect
@staff_member_required(redirect_field_name='referrer')
def changefile(request):
    # did it only for flake !
    file = CustomFileModel()
    file = CustomImageModel()

    if request.POST and request.is_ajax():
        folder = get_object_or_404(UserFolder, id=request.POST["folder"])
        if (request.user != folder.owner
                and not request.user.is_superuser):
            messages.add_message(
                request, messages.ERROR,
                _(u'You cannot access this folder.'))
            raise PermissionDenied

        file = get_object_or_404(
            eval(request.POST['file_type']), id=request.POST['file_id'])
        if (request.user != file.created_by
                and not request.user.is_superuser):
            messages.add_message(
                request, messages.ERROR,
                _(u'You cannot edit this file.'))
            raise PermissionDenied

        form_file = eval('%sForm' % request.POST['file_type'])(
            request.POST, request.FILES, instance=file)

        if form_file.is_valid():
            if form_file.cleaned_data["folder"] != folder:
                raise SuspiciousOperation('Folder must be the same')
            file = form_file.save(commit=False)
            if hasattr(form_file.instance, 'created_by'):
                file.created_by = form_file.instance.created_by
            else:
                file.created_by = request.user
            file.save()

            rendered = render_to_string(
                "podfile/list_folder_files.html",
                {'folder': folder,
                 }, request)

            list_element = {
                'list_element': rendered,
                'folder_id': folder.id
            }
            data = json.dumps(list_element)

            return HttpResponse(data, content_type='application/json')
        else:
            some_data_to_dump = {
                'errors': "%s" % _('Please correct errors'),
                'form_error': form_file.errors.as_json()
            }
            data = json.dumps(some_data_to_dump)
            return HttpResponse(data, content_type='application/json')
    else:
        raise SuspiciousOperation('You must send data in post')

    some_data_to_dump = {
        'status': "error",
        'response': ''
    }
    data = json.dumps(some_data_to_dump)

    return HttpResponse(data, content_type='application/json')


# keep it for completion part....
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
            "podfile/list_folder_files.html",
            {'folder': folder,
             }, request)

        list_element = {
            'list_element': rendered,
            'folder_id': folder.id
        }
        data = json.dumps(list_element)
        return HttpResponse(data, content_type='application/json')
    else:
        some_data_to_dump = {
            'errors': "%s" % _('Please correct errors'),
            'form_error': form_file.errors.as_json()
        }
        data = json.dumps(some_data_to_dump)
        return HttpResponse(data, content_type='application/json')

    return HttpResponse(data, content_type='application/json')


@csrf_protect
@staff_member_required(redirect_field_name='referrer')
def get_file(request, type):
    id = None
    if request.method == 'POST' and request.POST.get('src'):
        id = request.POST.get('src')
    elif request.method == 'GET' and request.GET.get('src'):
        id = request.GET.get('src')
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
                'id_file': reqfile.id,
                'id_folder': reqfile.folder.id,
                'response': fc
            }
    except OSError:
        some_data_to_dump = {
            'status': "error",
            'response': ''
        }
    data = json.dumps(some_data_to_dump)
    return HttpResponse(data, content_type='application/json')
