from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.core.exceptions import PermissionDenied
from django.http import HttpResponse
from django.template.loader import render_to_string
from django.shortcuts import render
from django.shortcuts import get_object_or_404
from django.utils.translation import ugettext as _
from django.views.decorators.csrf import csrf_protect
from pod.video.models import Video
from pod.enrichment.models import Enrichment
from pod.enrichment.forms import EnrichmentForm

import json

ACTION = ['new', 'save', 'modify', 'delete', 'cancel']


@csrf_protect
@login_required
@staff_member_required
def video_enrichment(request, slug):
    video = get_object_or_404(Video, slug=slug)
    if request.user != video.owner and not request.user.is_superuser:
        messages.add_message(
            request, messages.ERROR, _(u'You cannot enrich this video.'))
        raise PermissionDenied

    list_enrichment = video.enrichment_set.all()
    if request.POST and request.POST.get('action'):
        if request.POST['action'] in ACTION:
            return eval(
                'video_enrichment_{0}(request, video)'.format(
                    request.POST['action'])
            )
    else:
        return render(
            request,
            'video_enrichment.html',
            {'video': video,
             'list_enrichment': list_enrichment})


def video_enrichment_new(request, video):
    list_enrichment = video.enrichment_set.all()

    form_enrichment = EnrichmentForm(
        initial={'video': video, 'start': 0, 'end': 1})
    if request.is_ajax():
        return render(
            request,
            'enrichment/form_enrichment.html',
            {'video': video,
             'form_enrichment': form_enrichment})
    else:
        return render(
            request,
            'video_enrichment.html',
            {'video': video,
             'list_enrichment': list_enrichment,
             'form_enrichment': form_enrichment})


def video_enrichment_save(request, video):
    list_enrichment = video.enrichment_set.all()

    form_enrichment = None
    if request.POST.get('enrich_id') != 'None':
        enrich = get_object_or_404(
            Enrichment, id=request.POST['enrich_id'])
        form_enrichment = EnrichmentForm(request.POST, instance=enrich)
    else:
        form_enrichment = EnrichmentForm(request.POST)

    if form_enrichment.is_valid():
        form_enrichment.save()
        list_enrichment = video.enrichment_set.all()
        if request.is_ajax():
            some_data_to_dump = {
                'list_enrichment': render_to_string(
                    'enrichment/list_enrichment.html', {
                        'list_enrichment': list_enrichment, 'video': video
                    }),
                'player': render_to_string(
                    'videos/video_player.html', {
                        'video': video,
                        'csrf_token': request.COOKIES['csrftoken']
                    })
            }
            data = json.dumps(some_data_to_dump)
            return HttpResponse(data, content_type='application/json')
        else:
            return render(
                request,
                'video_enrichment.html',
                {'video': video,
                 'list_enrichment': list_enrichment})
    else:
        if request.is_ajax():
            some_data_to_dump = {
                'errors': '{0}'.format(_('Please correct errors.')),
                'form': render_to_string(
                    'enrichment/form_enrichment.html', {
                        'video': video, 'form_enrichment': form_enrichment
                    })
            }
            data = json.dumps(some_data_to_dump)
            return HttpResponse(data, content_type='application/json')
        else:
            return render(
                request,
                'video_enrichment.html',
                {'video': video,
                 'list_enrichment': list_enrichment,
                 'form_enrichment': form_enrichment})


def video_enrichment_modify(request, video):
    list_enrichment = video.enrichment_set.all()

    enrich = get_object_or_404(Enrichment, id=request.POST['id'])
    form_enrichment = EnrichmentForm(instance=enrich)
    if request.is_ajax():
        return render(
            request,
            'enrichment/form_enrichment.html',
            {'video': video,
             'form_enrichment': form_enrichment})
    else:
        return render(
            request,
            'video_enrichment.html',
            {'video': video,
             'list_enrichment': list_enrichment})


def video_enrichment_delete(request, video):
    enrich = get_object_or_404(Enrichment, id=request.POST['id'])
    enrich.delete()
    list_enrichment = video.enrichment_set.all()
    if request.is_ajax():
        some_data_to_dump = {
            'list_enrichment': render_to_string(
                'enrichment/list_enrichment.html', {
                    'list_enrichment': list_enrichment, 'video': video
                }),
            'player': render_to_string(
                'videos/video_player.html', {
                    'video': video, 'csrf_token': request.COOKIES['csrf_token']
                })
        }
        data = json.dumps(some_data_to_dump)
        return HttpResponse(data, content_type='application/json')
    else:
        return render(
            request,
            'video_enrichment.html',
            {'video': video,
             'list_enrichment': list_enrichment})


def video_enrichment_cancel(request, video):
    list_enrichment = video.enrichment_set.all()
    return render(
        request,
        'video_enrichment.html',
        {'video': video,
         'list_enrichment': list_enrichment})
