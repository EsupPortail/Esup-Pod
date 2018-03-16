"""
Custom File Picker for pod
Override FilePickerBase and ImagePickerBase

django-file-picker : 0.9.1.
"""
from django.conf import settings
from django.core.paginator import Paginator, EmptyPage
from django.core.urlresolvers import reverse
from django.db.models import Q
from django.http import HttpResponse, HttpResponseServerError
from django.middleware.csrf import get_token
from sorl.thumbnail.helpers import ThumbnailError
from sorl.thumbnail import get_thumbnail
from .forms import CustomFileForm, CustomImageForm
from .models import CustomFileModel, CustomImageModel

import file_picker
import os
import json
import tempfile
import logging
import datetime

logger = logging.getLogger(__name__)


class CustomFilePicker(file_picker.FilePickerBase):
    form = CustomFileForm
    columns = ('name', 'file_type', 'date_modified')
    extra_headers = ('Name', 'File type', 'Date modified', 'Delete')

    def append(self, obj, request):
        extra = {}
        for name in self.columns:
            value = getattr(obj, name)
            if isinstance(value, (datetime.datetime, datetime.date)):
                value = value.strftime('%b %d, %Y')
            else:
                value = str(value)
            extra[name] = value
        url = reverse('delete-files', kwargs={
            'file': str(getattr(obj, 'id')),
            'ext': str(getattr(obj, 'file_type'))
        })
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

    def upload_file(self, request):
        if 'userfile' in request.FILES:
            name, ext = os.path.splitext(request.FILES['userfile'].name)
            fn = tempfile.NamedTemporaryFile(
                prefix=name, suffix=ext, delete=False)
            f = request.FILES['userfile']
            for chunk in f.chunks():
                fn.write(chunk)
            fn.close()
            return HttpResponse(json.dumps({'name': fn.name}),
                                content_type='application/json')
        else:
            form = self.form(request.POST or None, initial={
                             'created_by': request.user.id})
            if form.is_valid():
                obj = form.save()
                data = self.append(obj, request)
                return HttpResponse(json.dumps(data),
                                    content_type='application/json')
            data = {'form': form.as_table()}
            return HttpResponse(json.dumps(data),
                                content_type='application/json')

    def get_queryset(self, search, user):
        qs = Q()
        if search:
            for name in self.field_names:
                comparision = {}
                comparision[name] = search
                qs = qs | Q(name_contains=search, created_by=user)
            queryset = self.model.objects.filter(qs)
        else:
            queryset = self.model.objects.filter(created_by=user)
        if self.ordering:
            queryset = queryset.order_by(self.ordering)
        else:
            queryset = queryset.order_by('-pk')
        return queryset

    def list(self, request):
        form = file_picker.forms.QueryForm(request.GET)
        if not form.is_valid():
            return HttpResponseServerError()
        page = form.cleaned_data['page']
        result = []
        qs = self.get_queryset(form.cleaned_data['search'], request.user)
        pages = Paginator(qs, self.page_size)
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


class CustomImagePicker(CustomFilePicker):
    form = CustomImageForm
    link_headers = ['Thumbnail', ]

    def append(self, obj, request):
        json = super(CustomImagePicker, self).append(obj, request)
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


file_picker.site.register(CustomFileModel, CustomFilePicker, name='file')
file_picker.site.register(CustomImageModel, CustomImagePicker, name='img')


def delete(request, file, ext):
    data = {}
    if ext in ['JPG', 'BMP', 'GIF', 'JPEG']:
        obj = CustomImageModel.objects.get(id=file, file_type=ext)
    else:
        obj = CustomFileModel.objects.get(id=file, file_type=ext)
    path = os.path.join(settings.MEDIA_ROOT, obj.file.url.strip('/media/'))
    if os.path.exists(path):
        os.remove(path)
        obj.delete()
        data['status'] = 'OK'
        return HttpResponse(json.dumps(data), content_type='application/json')
    else:
        data['status'] = 'ERROR'
        return HttpResponse(json.dumps(data), content_type='application/json')
