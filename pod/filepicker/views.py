"""
Custom File Picker for pod
Override FilePickerBase and ImagePickerBase

django-file-picker : 0.9.1.
"""
from django.conf.urls import url
from django.conf import settings
from django.core.paginator import Paginator, EmptyPage
from django.core.urlresolvers import reverse
from django.db import models
from django.db.models import Q
from django.db.models.base import FieldDoesNotExist
from django.http import HttpResponse
from django.http import HttpResponseServerError
from django.http import HttpResponseBadRequest
from django.http import HttpResponseNotFound
from django.middleware.csrf import get_token
from django.utils.text import capfirst
from django.utils.translation import ugettext as _
from django.shortcuts import get_object_or_404
from sorl.thumbnail.helpers import ThumbnailError
from sorl.thumbnail import get_thumbnail
from pod.filepicker.forms import AjaxItemForm
from pod.filepicker.forms import QueryForm


import os
import json
import tempfile
import logging
import datetime
import traceback

logger = logging.getLogger(__name__)

FIELD_EXCLUDES = (models.ImageField, models.FileField,)

FILE_MAX_UPLOAD_SIZE = getattr(
    settings, 'FILE_MAX_UPLOAD_SIZE', 100)


def model_to_AjaxItemForm(model):
    exclude = list()
    for field_name in [f.name for f in model._meta.get_fields()]:
        try:
            field = model._meta.get_field(field_name)
        except FieldDoesNotExist:
            exclude.append(field_name)
            continue
        if isinstance(field, FIELD_EXCLUDES):
            exclude.append(field_name)
    meta = type('Meta', (), {'model': model, 'exclude': exclude})
    modelform_class = type('modelform', (AjaxItemForm,), {'Meta': meta})
    return modelform_class


class FilePickerBase(object):
    """
    The FilePicker main class.

    Parameters
    ----------
    name : str
        The name of this FilePicker instance
    model : django.db.models.base.ModelBase
        BaseFileModel
    structure : django.db.models.base.ModelBase
        UserDirectory
    configure : django.forms.models.ModelFormMetaclass
        UserDirectoryForm

    Self
    ----
    Previously explained fields : name, model, structure, configure AND

    form : AjaxItemForm
        The file form
    field_names : list
        List of field names from model
    columns : list
        List of fields which will be used and displayed 
        in the file browser interface
    """

    model = None
    form = None
    structure = None
    configure = None
    page_size = 4
    link_headers = ['Insert File', ]
    extra_headers = None
    columns = None
    ordering = None

    def __init__(self, name, model, structure, configure):
        self.name = name
        self.model = model
        self.structure = structure
        self.configure = configure
        if not self.form:
            self.form = model_to_AjaxItemForm(self.model)
        self.field_names = [f.name for f in model._meta.get_fields()]
        if not self.columns:
            self.columns = self.field_names
        self.populate_field(model)
        self.verify_column(model)

    def populate_field(self, model):
        """
        Function that find a File or Image field in the model and create a 
        variable to access it more easily.
        Delete from field_name all ForeignKey and ManyToMany fields. 

        Parameters
        ----------
        model : django.db.models.base.ModelBase
            BaseFileModel
        """

        for field_name in self.field_names:
            field = model._meta.get_field(field_name)
            if isinstance(field, (models.ImageField, models.FileField)):
                self.field = field_name
        for field_name in self.field_names:
            if isinstance(field, (models.ForeignKey, models.ManyToManyField)):
                self.field_names.remove(field_name)

    def verify_column(self, model):
        """
        Function that checks the fields in the columns variable. Remove all
        incorrect fields.
        If build_headers is true, the verbose name of this fields are used
        to name the column headers in the file browser interface.

        Parameters
        ----------
        model : django.db.models.base.ModelBase
            BaseFileModel
        """

        build_headers = not self.columns or not self.extra_headers
        extra_headers = list()
        for field_name in self.columns:
            try:
                field = model._meta.get_field(field_name)
            except models.FileDoesNotExist:
                self.field_names.remove(field_name)
                continue
            extra_headers.append(capfirst(field.verbose_name))
        if build_headers:
            self.extra_headers = extra_headers

    def protect(self, view, csrf_exempt=False):
        """
        Function that protect a view with a csrf_token.

        Parameters
        ----------
        view : function
            A view function
        csrf_exempt : boolean
            True - csrf_token needed for the view
            False - csrf_token disabled for the view

        Return
        ------
        function : wrapper
            return the view if correct
            return an HttpResponse with a exception if not
        """

        def wrapper(*args, **kwargs):
            data = dict()
            try:
                return view(*args, **kwargs)
            except Exception as e:
                logger.exception('Error in view')
                data['errors'] = [traceback.format_exc(e)]
            return HttpResponse(
                json.dumps(data),
                content_type='application/json')

        wrapper.csrf_exempt = csrf_exempt
        return wrapper

    def get_urls(self):
        """
        Function that define the urls used by the apps.

        Return
        ------
        tuple
            The urlpatterns associated to this FilePickerBase instance
        """

        urlpatterns = [
            url(r'^$', self.setup, name='init'),
            url(r'^files/$', self.list, name='list-files'),
            url(r'^file/$',
                self.get_file, name='get-file'),
            url(r'^upload/file/$', self.protect(self.upload_file, True),
                name='upload-file'),
            url(r'^delete/file/(?P<file>[\-\d\w]+)/$', self.delete,
                name='delete-file'),
            url(r'^directories/$',
                self.list_dirs, name='list-directories'),
            url(r'^directories/configure/$',
                self.protect(self.conf_dirs, True),
                name='configure-directories'),
        ]
        return (urlpatterns, None, self.name)

    urls = property(get_urls)

    def setup(self, request):
        """
        Function that builds the urls needed by FilePicker front-end.
        The urls are defined as follows :
            'filepicker:<FilePickerBase instance name>:<url name>'
        By default :
            'browse': view(s) that get information about files
            'upload': view(s) that adds files
            'directories': view(s) that manages the user directories

        Parameters
        ----------
        request : RequestObject

        Return
        ------
        HttpResponse
            List of urls in a dictionnary
        """

        data = dict()
        data['urls'] = {
            'browse': {
                'files': reverse(
                    'filepicker:{0}:list-files'.format(self.name)),
                'file': reverse(
                    'filepicker:{0}:get-file'.format(self.name))
            },
            'upload': {
                'file': reverse(
                    'filepicker:{0}:upload-file'.format(self.name))
            },
            'directories': {
                'file': reverse(
                    'filepicker:{0}:list-directories'.format(self.name)),
                'configure': reverse(
                    'filepicker:{0}:configure-directories'.format(self.name))
            },
        }
        return HttpResponse(json.dumps(data), content_type='application/json')

    def append(self, obj, request):
        """
        Function that return information about files.

        Parameters
        ----------
        obj : CustomFileModel
            A file
        request : RequestObject

        Return
        ------
        dictionnary : { 
            name : name of file,
            url : url to this file,
            extra : {
                name : name of file,
                file_type : type of file (extension),
                data_modified : last modification (MM/DD/YY),
                delete : delete form for this file,
                id : file identifier
            },
            insert : [
                url to this file
            ],
            link_content : The message on the button who
                insert the file
        }
        """

        extra = {}
        for name in self.columns:
            value = getattr(obj, name)
            if isinstance(value, (datetime.datetime, datetime.date)):
                value = value.strftime('%b %d, %Y')
            else:
                value = str(value)
            extra[name] = value
        url = reverse(
            'filepicker:{0}:delete-file'.format(self.name),
            kwargs={'file': str(getattr(obj, 'id'))}
        )
        extra['delete'] = '<form action="' + url + '">'
        extra['delete'] += '<input type="hidden" name="' + \
            'csrfmiddlewaretoken" value="' + get_token(request) + '">'
        extra['delete'] += '<button type="button" ' + \
            'class="delete-file btn btn-danger">' + \
            'Delete</button></form>'
        extra['id'] = str(getattr(obj, 'id'))
        return {
            'name': str(obj),
            'url': getattr(obj, self.field).url,
            'extra': extra,
            'insert': [getattr(obj, self.field).url, ],
            'link_content': ['Click to insert'],
        }

    def conf_dirs(self, request):
        """
        View that manage actions on directories : edit, new and delete

        Parameters
        ----------
        request : RequestObject

        Return
        ------
        HttpResponse
        """

        if request.GET and request.GET.get('action'):
            if request.GET['action'] == 'edit':
                try:
                    directory = self.structure.objects.get(
                        owner=request.user.id,
                        id=request.GET['id'])
                except Exception:
                    return HttpResponseNotFound('Directory not found !')
                form = self.configure(instance=directory)
                data = {'form': form.as_table(), 'id': directory.id}
                return HttpResponse(
                    json.dumps(data), content_type='application/json')
            if request.GET['action'] == 'new':
                try:
                    directory = self.structure.objects.get(
                        owner=request.user.id,
                        id=request.GET['id'])
                except Exception:
                    return HttpResponseNotFound('Directory not found !')
                form = self.configure(initial={
                    'owner': request.user.id,
                    'parent': directory})
                data = {'form': form.as_table()}
                return HttpResponse(
                    json.dumps(data), content_type='application/json')
            if request.GET['action'] == 'delete':
                try:
                    directory = self.structure.objects.get(
                        owner=request.user.id,
                        id=request.GET['id'])
                except Exception:
                    return HttpResponseNotFound('Directory not found !')
                data = {'id': directory.id}
                return HttpResponse(
                    json.dumps(data), content_type='application/json')
        if request.POST and request.POST.get('action'):
            if request.POST['action'] == 'edit':
                try:
                    directory = self.structure.objects.get(
                        owner=request.user.id,
                        id=request.POST['id'])
                except Exception:
                    return HttpResponseNotFound('Directory not found !')
                form = self.configure(request.POST, instance=directory)
                if form.is_valid():
                    form.save()
                    data = {'response': 'OK'}
                    return HttpResponse(json.dumps(data),
                                        content_type='application/json')
                else:
                    data = {'form': form.as_table(),
                            'errors': form.errors}
                    return HttpResponse(
                        json.dumps(data), content_type='application/json')
            if request.POST['action'] == 'new':
                form = self.configure(request.POST)
                if form.is_valid():
                    directory = form.save()
                    data = {'parent': directory.parent.name}
                    return HttpResponse(json.dumps(data),
                                        content_type='application/json')
                else:
                    data = {'form': form.as_table(),
                            'errors': form.errors}
                    return HttpResponse(
                        json.dumps(data), content_type='application/json')
            if request.POST['action'] == 'delete':
                try:
                    directory = self.structure.objects.get(
                        id=request.POST['id'])
                except Exception:
                    return HttpResponseNotFound('Directory not found !')
                if directory.name != 'Home':
                    directory.delete()
                else:
                    return HttpResponseBadRequest(
                        'Home directory cannot be deleted !')
                data = {'parent': directory.parent.name}
                return HttpResponse(
                    json.dumps(data), content_type='application/json')
        return HttpResponseBadRequest('Bad request')

    def get_files(self, search, user, directory):
        """
        Function that returns one or more files according to a search
        pattern given by the user. If no search pattern, returns all files of
        a user. 
        Files can be returned in a specific order.
        In any case the queries are made in a single directory.

        Parameters
        ----------
        search : str
            Search pattern (by title)
        user : User
            User request object
        directory : UserDirectory
            The directory where we are looking

        Return
        ------
        queryset
            Set of found files
        """

        qs = Q()
        if search:
            for name in self.field_names:
                comparision = dict()
                comparision[name] = search
                qs = qs | Q(
                    name__contains=search,
                    created_by=user,
                    directory=directory)
            queryset = self.model.objects.filter(qs)
        else:
            queryset = self.model.objects.filter(
                created_by=user,
                directory=directory)
        if self.ordering:
            queryset = queryset.order_by(self.ordering)
        else:
            queryset = queryset.order_by('-pk')
        return queryset

    def get_file(self, request):
        """
        View that return information on a single file.

        Parameters
        ----------
        request : RequestObject

        Return
        ------
        HttpResponse
            A dictionnary with information about this file
            {
                name : filename (filetype),
                thumbnail : url of the thumbnail
            }
        """

        if not request.GET or not request.GET.get('id'):
            return HttpResponseBadRequest('Bad request')
        else:
            result = get_object_or_404(self.model, id=request.GET['id'])
            data = {'result': {
                'name': '{0} ({1}) '.format(result.name, result.file_type),
                'thumbnail': '/static/img/file.png'
            }
            }
            return HttpResponse(
                json.dumps(data), content_type='application/json')

    def get_dirs(self, user, directory=None):
        """
        Function that return information about a specific directory otherwise 
        about the Home directory.

        Parameters
        ----------
        user : User
            User request object
        directory : UserDirectory
            The desired directory or None

        Return
        ------
        dictionnary
            A dictionnary with informations about the directory. Exemple with
            Home :
            {
                Home : [
                    {
                        name : children name,
                        last : if this children don't have children himself,
                        size : number of files in this children,
                        id : children identifier
                    },
                    {
                        ...
                    }
                ],
                path : the path to this directory,
                parent : name of the parent of this directory,
                size : number of files in this directory,
                id : directory identifier
            }
        """

        if directory:
            current = self.structure.objects.get(
                owner=user, id=directory)
        else:
            current = self.structure.objects.get(
                owner=user, name='Home')

        parent = current.parent if current.parent else current
        children = current.children.all()

        response = dict()
        response[current.name] = list()
        response['path'] = current.get_path()
        response['parent'] = parent.name
        response['size'] = self.model.objects.filter(
            directory=current, created_by=user).count()
        response['id'] = parent.id
        if children:
            for child in children:
                response[current.name].append({
                    'name': child.name,
                    'last': False if child.children.all() else True,
                    'size': self.model.objects.filter(
                        directory=child,
                        created_by=user).count(),
                    'id': child.id,
                })
        return response

    def list_dirs(self, request):
        """
        View that return a list of directory

        Parameters
        ----------
        request : RequestObject

        Return
        ------
        HttpResponse
            The list of directory according to the current position
            of the user in his tree
        """

        if request.GET.get('directory'):
            directory = request.GET['directory']
            response = self.get_dirs(request.user, directory)
        else:
            response = self.get_dirs(request.user)
        data = {'result': response}
        return HttpResponse(json.dumps(data), content_type='application/json')

    def upload_file(self, request):
        """
        View that manage the uploading of files

        Parameters
        ----------
        request : RequestObject

        Return
        ------
        HttpResponse
        """

        if 'userfile' in request.FILES:
            name, ext = os.path.splitext(request.FILES['userfile'].name)
            fn = tempfile.NamedTemporaryFile(
                prefix=name, suffix=ext, delete=False)
            f = request.FILES['userfile']
            if f.size > FILE_MAX_UPLOAD_SIZE * 1024 * 1024:
                return HttpResponse(
                    json.dumps(
                        {'errors': _('File size is too large (>100MB)')}),
                    content_type='application/json')
            for chunk in f.chunks():
                fn.write(chunk)
            fn.close()
            return HttpResponse(
                json.dumps({'name': fn.name}),
                content_type='application/json')
        else:
            if request.method == 'POST':
                form = self.form(request.POST, initial={
                    'created_by': request.user,
                    'directory': request.POST['directory']
                })
                if form.is_valid():
                    obj = form.save()
                    data = self.append(obj, request)
                    return HttpResponse(
                        json.dumps(data),
                        content_type='application/json')
                else:
                    errors = dict()
                    for name, error in form.errors.items():
                        errors[name] = error
                    data = {'errors': errors}
                    return HttpResponse(
                        json.dumps(data),
                        content_type='application/json')
            else:
                if request.GET.get('directory'):
                    directory = self.structure.objects.get(
                        owner=request.user, id=request.GET['directory'])
                else:
                    directory = self.structure.objects.get(
                        owner=request.user, name='Home')
                form = self.form(
                    initial={'created_by': request.user,
                             'directory': directory.id})

            data = {'form': form.as_table()}
            return HttpResponse(
                json.dumps(data),
                content_type='application/json')

    def list(self, request):
        """
        View that return a list of files according to the current position
        of the user in his directories tree

        Parameters
        ----------
        request : RequestObject

        Return
        ------
        HttpResponse
            A dictionnary with the list of files :
            {
                page : current page number,
                pages : number of page,
                search : the search pattern possibly filled by the user,
                result : queryset of found files,
                has_next : if page after the current page,
                has_previous : if page before the current page,
                link_headers : headers for the insert file link cell of the
                    file table,
                extra_headers : headers for the columns of the file table,
                columns : data of the files that will be displayed
            }
        """

        form = QueryForm(request.GET)
        if not form.is_valid():
            return HttpResponseServerError()
        page = form.cleaned_data['page']
        result = []

        if request.GET.get('directory'):
            directory = request.GET['directory']
            files = self.get_files(
                form.cleaned_data['search'], request.user, directory)
        else:
            directory = self.structure.objects.get(
                owner=request.user, name='Home').id
            files = self.get_files(
                form.cleaned_data['search'], request.user, directory)
        pages = Paginator(files, self.page_size)
        try:
            page_obj = pages.page(page)
        except EmptyPage:
            return HttpResponseServerError()
        for obj in page_obj.object_list:
            result.append(self.append(obj, request))
        columns = self.columns + ('delete',)
        data = {
            'page': page,
            'pages': list(pages.page_range),
            'search': form.cleaned_data['search'],
            'result': result,
            'has_next': page_obj.has_next(),
            'has_previous': page_obj.has_previous(),
            'link_headers': self.link_headers,
            'extra_headers': self.extra_headers,
            'columns': columns,
        }
        return HttpResponse(json.dumps(data), content_type='application/json')

    def delete(self, request, file):
        """
        View that manages the deletion of files

        Parameters
        ----------
        request : RequestObject
        file : int
            Identifier of the file to delete

        Return
        ------
        HttpResponse
        """

        if request.method == 'POST':
            self.model.objects.get(id=file).delete()
            data = {'status': 'OK'}
            return HttpResponse(
                json.dumps(data),
                content_type='application/json')
        return HttpResponseBadRequest()


class ImagePickerBase(FilePickerBase):
    """
    The ImagePicker main class. Extend FilePickerBase.

    Parameters
    ----------
    name : str
        The name of this ImagePicker instance
    model : django.db.models.base.ModelBase
        BaseFileModel
    structure : django.db.models.base.ModelBase
        UserDirectory
    configure : django.forms.models.ModelFormMetaclass
        UserDirectoryForm

    Self
    ----
    Previously explained fields : name, model, structure, configure AND

    form : AjaxItemForm
        The file form
    field_names : list
        List of field names from model
    columns : list
        List of fields which will be used and displayed 
        in the file browser interface
    """

    link_headers = ['Thumbnail', ]

    def append(self, obj, request):
        """
        Function that return information about images.

        Parameters
        ----------
        obj : CustomImageModel
            A image
        request : RequestObject

        Return
        ------
        dictionnary : { 
            name : name of image,
            url : url to this image,
            extra : {
                name : name of image,
                file_type : type of image (extension),
                data_modified : last modification (MM/DD/YY),
                delete : delete form for this image,
                id : image identifier
            },
            insert : [
                url to this image for thumbnail
            ],
            link_content : Thumbnail on the button who insert the image
        }
        """
        json = super(ImagePickerBase, self).append(obj, request)
        img = '<img src="{0}" alt="{1}" width="{2}" height="{3}" />'
        try:
            thumb = get_thumbnail(obj.file.path, '100x100',
                                  crop='center', quality=99)
        except ThumbnailError:
            logger.exception()
            thumb = None
        if thumb:
            json['link_content'] = [img.format(
                thumb.url, 'image', thumb.width, thumb.height), ]
        else:
            json['link_content'] = [img.format('', 'Not Found', 100, 100), ]
        return json

    def get_file(self, request):
        """
        View that return information on a single image.

        Parameters
        ----------
        request : RequestObject

        Return
        ------
        HttpResponse
            A dictionnary with information about this image
            {
                name : image name (filetype),
                thumbnail : url of the thumbnail
            }
        """
        if not request.GET or not request.GET.get('id'):
            return HttpResponseBadRequest('Bad request')
        else:
            result = get_object_or_404(self.model, id=request.GET['id'])
            try:
                thumb = get_thumbnail(result.file.path, '100x100',
                                      crop='center', quality=99)
            except ThumbnailError:
                logger.exception()
                thumb = None
            if thumb:
                url = thumb.url
            else:
                url = '/static/img/picture.png'
            data = {'result': {
                'name': '{0} ({1}) '.format(result.name, result.file_type),
                'thumbnail': url
            }
            }
            return HttpResponse(
                json.dumps(data), content_type='application/json')
