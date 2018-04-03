from django.conf.urls import url
from django.core.urlresolvers import reverse, NoReverseMatch
from django.db import models
from django.db.models.base import ModelBase, FieldDoesNotExist
from django.http import HttpResponse
from pod.filepicker.views import FilePickerBase
from pod.filepicker.views import ImagePickerBase

import json


class FilePickerSite(object):

    def __init__(self, name=None, app_name='filepicker'):
        self._registry = []

    def guess_default(self, model):
        for field_name in model._meta.get_all_field_names():
            try:
                field = model._meta.get_field(field_name)
            except FieldDoesNotExist:
                continue
            if isinstance(field, models.ImageField):
                return ImagePickerBase
            elif isinstance(field, models.FileField):
                return FilePickerBase
        return FilePickerBase

    def register(self, model_or_iterable, class_=None, name=None, structure=None, **options):
        if isinstance(model_or_iterable, ModelBase):
            model_or_iterable = [model_or_iterable]
        for model in model_or_iterable:
            if not name:
                view_name = class_.__class__.__name__.lower()
                model_name = model().__class__.__name__.lower()
                name = "%s-%s" % (model_name, view_name)
            if class_:
                picker_class = class_
            else:
                picker_class = self.guess_default(model)
            self._registry.append(
                {'name': name, 'picker': picker_class(name, model, structure)})

    def get_urls(self):
        urlpatterns = [
            url(r'^$', self.primary, name='index'),
        ]
        for p in self._registry:
            urlpatterns += url(r'^%s/' % p['name'], p['picker'].urls),
        return (urlpatterns, None, "filepicker")
    urls = property(get_urls)

    def primary(self, request):
        picker_names = request.GET.getlist('pickers')
        pickers = {}
        for name in picker_names:
            try:
                pickers[name] = reverse('filepicker:%s:init' % name)
            except NoReverseMatch:
                pickers[name] = None
        data = {'pickers': pickers}
        return HttpResponse(json.dumps(data), content_type='application/json')


site = FilePickerSite()
