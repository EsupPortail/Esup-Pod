"""
Custom File Picker for pod
Override FilePickerBase and ImagePickerBase

django-file-picker : 0.9.1.
"""
from django.core.paginator import Paginator, EmptyPage
from django.db.models import Q
from django.http import HttpResponse, HttpResponseServerError
from .forms import CustomFileForm, CustomImageForm
from .models import CustomFileModel, CustomImageModel

import file_picker
import os
import json
import tempfile


class CustomFilePicker(file_picker.FilePickerBase):
    form = CustomFileForm
    columns = ('name', 'file_type', 'date_modified')
    extra_headers = ('Name', 'File type', 'Date modified')

    def upload_file(self, request):
        if 'userfile' in request.FILES:
            name, ext = os.path.splitext(request.FILES['userfile'].name)
            fn = tempfile.NamedTemporaryFile(
                prefix=name, suffix=ext, delete=False)
            f = request.FILES['userfile']
            for chunk in f.chunks():
                fn.write(chunk)
            fn.close()
            return HttpResponse(json.dumps({'name': fn.name}), content_type='application/json')
        else:
            form = self.form(request.POST or None, initial={
                             'created_by': request.user.id})
            if form.is_valid():
                obj = form.save()
                data = self.append(obj)
                return HttpResponse(json.dumps(data), content_type='application/json')
            data = {'form': form.as_table()}
            return HttpResponse(json.dumps(data), content_type='application/json')

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
            result.append(self.append(obj))
        data = {
            'page': page,
            'pages': list(pages.page_range),
            'search': form.cleaned_data['search'],
            'result': result,
            'has_next': page_obj.has_next(),
            'has_previous': page_obj.has_previous(),
            'link_headers': self.link_headers,
            'extra_headers': self.extra_headers,
            'columns': self.columns,
        }
        return HttpResponse(json.dumps(data), content_type='application/json')

class CustomImagePicker(CustomFilePicker):
	form = CustomImageForm
	link_headers =['Thumbnail',]

file_picker.site.register(CustomFileModel, CustomFilePicker, name='file')
file_picker.site.register(CustomImageModel, CustomImagePicker, name='img')
