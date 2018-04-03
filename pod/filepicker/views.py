"""
Custom File Picker for pod
Override FilePickerBase and ImagePickerBase

django-file-picker : 0.9.1.
"""
from django.conf import settings
from django.conf.urls import url
from django.core.paginator import Paginator, EmptyPage
from django.core.urlresolvers import reverse
from django.db import models
from django.db.models import Q
from django.db.models.base import FieldDoesNotExist
from django.http import HttpResponse, HttpResponseServerError
from django.middleware.csrf import get_token
from django.utils.text import capfirst
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
    model = None
    form = None
    structure = None
    page_size = 4
    link_headers = ['Insert File', ]
    extra_headers = None
    columns = None
    ordering = None

    def __init__(self, name, model, structure):
        self.name = name
        self.model = model
        self.structure = structure
        if not self.form:
            self.form = model_to_AjaxItemForm(self.model)
        self.field_names = [f.name for f in model._meta.get_fields()]
        build_headers = not self.columns or not self.extra_headers
        if not self.columns:
            self.columns = self.field_names
        extra_headers = list()
        for field_name in self.field_names:
            field = model._meta.get_field(field_name)
            if isinstance(field, (models.ImageField, models.FileField)):
                self.field = field_name
        for field_name in self.field_names:
            try:
                field = model._meta.get_field(field_name)
            except models.FieldDoesNotExist:
                self.field_names.remove(field_name)
                continue
            if isinstance(field, (models.ForeignKey, models.ManyToManyField)):
                self.field_names.remove(field_name)
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
        urlpatterns = [
            url(r'^$', self.setup, name='init'),
            url(r'^files/$', self.list, name='list-files'),
            url(r'^upload/file/$', self.protect(self.upload_file, True),
                name='upload-file'),
            url(r'^delete/file/(?P<file>[\-\d\w]+)/$', self.delete,
                name='delete-file'),
            url(r'^directories/$',
                self.list_dirs, name='list-directories'),
        ]
        return (urlpatterns, None, self.name)

    urls = property(get_urls)

    def setup(self, request):
        data = dict()
        data['urls'] = {
            'browse': {
                'files': reverse(
                    'filepicker:{0}:list-files'.format(self.name))
            },
            'upload': {
                'file': reverse(
                    'filepicker:{0}:upload-file'.format(self.name))
            },
            'directories': {
                'file': reverse(
                    'filepicker:{0}:list-directories'.format(self.name))
            },
        }
        return HttpResponse(json.dumps(data), content_type='application/json')

    def append(self, obj, request):
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
        extra['delete'] += '<button type="button" class="delete">' + \
            'Delete</button></form>'
        return {
            'name': str(obj),
            'url': getattr(obj, self.field).url,
            'extra': extra,
            'insert': [getattr(obj, self.field).url, ],
            'link_content': ['Click to insert'],
        }

    def get_files(self, search, user, directory='Home'):
        qs = Q()
        if search:
            for name in self.field_names:
                comparision = dict()
                comparision[name] = search
                qs = qs | Q(
                    name_contains=search,
                    created_by=user,
                    directory__name=directory)
            queryset = self.model.objects.filter(qs)
        else:
            queryset = self.model.objects.filter(
                created_by=user,
                directory__name=directory)
        if self.ordering:
            queryset = queryset.order_by(self.ordering)
        else:
            queryset = queryset.order_by('-pk')
        return queryset

    def get_dirs(self, user, directory):
        current = self.structure.objects.get(
            owner__user=user, name=directory)
        parent = current.parent.name if current.parent else directory
        children = current.children.all()
        response = dict()
        if children:
            response[directory] = list()
            response['parent'] = parent
            for child in children:
                response[directory].append({
                    'name': child.name,
                    'last': False if child.children.all() else True,
                    'size': self.model.objects.filter(
                        directory__name=child.name).count(),
                })
        return response

    def list_dirs(self, request):
        response = self.get_dirs(request.user, request.GET['directory'])
        data = {'result': response}
        return HttpResponse(json.dumps(data), content_type='application/json')

    def upload_file(self, request):
        if 'userfile' in request.FILES:
            name, ext = os.path.splitext(request.FILES['userfile'].name)
            fn = tempfile.NamedTemporaryFile(
                prefix=name, suffix=ext, delete=False)
            f = request.FILES['userfile']
            for chunk in f.chunks():
                fn.write(chunk)
            fn.close()
            return HttpResponse(
                json.dumps({'name': fn.name}),
                content_type='application/json')
        else:
            form = self.form(
                request.POST or None,
                initial={'created_by': request.user.id})
            if form.is_valid():
                obj = form.save()
                data = self.append(obj, request)
                return HttpResponse(
                    json.dumps(data),
                    content_type='application/json')
            data = {'form': form.as_table()}
            return HttpResponse(
                json.dumps(data),
                content_type='application/json')

    def list(self, request):
        form = QueryForm(request.GET)
        if not form.is_valid():
            return HttpResponseServerError()
        page = form.cleaned_data['page']
        result = []
        files = self.get_files(
            form.cleaned_data['search'], request.user, request.GET['directory'])
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
        f = self.model.objects.get(id=file)
        if os.path.isfile(f.path):
            os.remove(f.path)
            f.delete()
            data = {'status': 'OK'}
            return HttpResponse(
                json.dumps(data),
                content_type='application/json')
        else:
            return HttpResponseServerError()


class ImagePickerBase(FilePickerBase):
    link_headers = ['Thumbnail', ]

    def append(self, obj, request):
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
