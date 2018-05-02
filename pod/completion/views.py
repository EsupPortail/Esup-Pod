from django.contrib import messages
from django.http import HttpResponse
from django.http import HttpResponseForbidden
from django.http import HttpResponseBadRequest
from django.template.loader import render_to_string
from django.shortcuts import render
from django.shortcuts import get_object_or_404
from django.utils.translation import ugettext as _
from django.views.decorators.csrf import csrf_protect
from pod.video.models import Video
from pod.completion.models import Contributor
from pod.completion.forms import ContributorForm
from pod.completion.models import Document
from pod.completion.forms import DocumentForm
from pod.completion.models import Track
from pod.completion.forms import TrackForm
from pod.completion.models import Overlay
from pod.completion.forms import OverlayForm

import json


@csrf_protect
def video_completion(request, slug):
    if not request.user.is_authenticated():
        return HttpResponseForbidden('You need to be authenticated.')
    video = get_object_or_404(Video, slug=slug)

    if request.user != video.owner.user and not request.user.is_superuser:
        messages.add_message(
            request, messages.ERROR, _(u'You cannot complement this video.'))
        return HttpResponseForbidden('Only the owner can add completion.')
    elif request.user.is_staff:
        list_contributor = video.contributor_set.all()
        list_track = video.track_set.all()
        list_document = video.document_set.all()
        list_overlay = video.overlay_set.all()
    else:
        list_contributor = video.contributor_set.all()

    if request.user.is_staff:
        return render(
            request,
            'video_completion.html',
            {'video': video,
             'list_contributor': list_contributor,
             'list_track': list_track,
             'list_document': list_document,
             'list_overlay': list_overlay})
    else:
        return render(
            request,
            'video_completion.html',
            {'video': video,
             'list_contributor': list_contributor})


@csrf_protect
def video_completion_contributor(request, slug):
    if not request.user.is_authenticated():
        return HttpResponseForbidden()
    video = get_object_or_404(Video, slug=slug)
    if request.user != video.owner.user and not request.user.is_superuser:
        messages.add_message(
            request, messages.ERROR, _(u'You cannot complement this video.'))
        return HttpResponseForbidden()

    list_contributor = video.contributor_set.all()
    list_track = video.track_set.all()
    list_document = video.document_set.all()
    list_overlay = video.overlay_set.all()

    if request.POST and request.POST.get('action'):
        try:
            func = getattr(
                'pod.filepicker.views',
                'video_completion_contributor_{0}'.format(
                    request.POST['action']))
        except AttributeError:
            return HttpResponseBadRequest()
        else:
            return func(request, video)
    else:
        return render(
            request,
            'video_completion.html',
            {'video': video,
             'list_contributor': list_contributor,
             'list_document': list_document,
             'list_track': list_track,
             'list_overlay': list_overlay})


def video_completion_contributor_new(request, video):
    list_contributor = video.contributor_set.all()
    list_track = video.track_set.all()
    list_document = video.document_set.all()
    list_overlay = video.overlay_set.all()

    form_contributor = ContributorForm(initial={'video': video})
    if request.is_ajax():
        return render(
            request,
            'contributor/form_contributor.html',
            {'form_contributor': form_contributor,
             'video': video})
    else:
        return render(
            request,
            'video_completion.html',
            {'video': video,
             'list_contributor': list_contributor,
             'form_contributor': form_contributor,
             'list_track': list_track,
             'list_document': list_document,
             'list_overlay': list_overlay})


def video_completion_contributor_save(request, video):
    list_contributor = video.contributor_set.all()
    list_track = video.track_set.all()
    list_document = video.document_set.all()
    list_overlay = video.overlay_set.all()

    form_contributor = None
    if (request.POST.get('contributor_id') and
            request.POST['contributor_id'] != 'None'):
        contributor = get_object_or_404(
            Contributor, id=request.POST['contributor_id'])
        form_contributor = ContributorForm(
            request.POST, instance=contributor)
    else:
        form_contributor = ContributorForm(request.POST)
    if form_contributor.is_valid():
        form_contributor.save()
        list_contributor = video.contributor_set.all()
        if request.is_ajax():
            some_data_to_dump = {'list_data': render_to_string(
                'contributor/list_contributor.html',
                {'list_contributor': list_contributor,
                 'video': video},
                request=request),
            }
            data = json.dumps(some_data_to_dump)
            return HttpResponse(data, content_type='application/json')
        else:
            return render(
                request,
                'video_completion.html',
                {'video': video,
                 'list_contributor': list_contributor,
                 'list_document': list_document,
                 'list_track': list_track,
                 'list_overlay': list_overlay})
    else:
        if request.is_ajax():
            some_data_to_dump = {
                'errors': '{0}'.format(_('Please correct errors')),
                'form': render_to_string(
                    'contributor/form_contributor.html',
                    {'video': video,
                     'form_contributor': form_contributor},
                    request=request)
            }
            data = json.dumps(some_data_to_dump)
            return HttpResponse(data, content_type='application/json')
        return render(
            request,
            'video_completion.html',
            {'video': video,
             'list_contributor': list_contributor,
             'form_contributor': form_contributor,
             'list_document': list_document,
             'list_track': list_track,
             'list_overlay': list_overlay})


def video_completion_contributor_modify(request, video):
    list_contributor = video.contributor_set.all()
    list_track = video.track_set.all()
    list_document = video.document_set.all()
    list_overlay = video.overlay_set.all()

    contributor = get_object_or_404(
        Contributor, id=request.POST['id'])
    form_contributor = ContributorForm(instance=contributor)
    if request.is_ajax():
        return render(
            request,
            'contributor/form_contributor.html',
            {'form_contributor': form_contributor,
             'video': video})
    return render(
        request,
        'video_completion.html',
        {'video': video,
         'list_contributor': list_contributor,
         'form_contributor': form_contributor,
         'list_document': list_document,
         'list_track': list_track,
         'list_overlay': list_overlay})


def video_completion_contributor_delete(request, video):
    list_contributor = video.contributor_set.all()
    list_track = video.track_set.all()
    list_document = video.document_set.all()
    list_overlay = video.overlay_set.all()

    contributor = get_object_or_404(
        Contributor, id=request.POST['id'])
    contributor.delete()
    list_contributor = video.contributor_set.all()
    if request.is_ajax():
        some_data_to_dump = {
            'list_data': render_to_string(
                'contributor/list_contributor.html',
                {'list_contributor': list_contributor,
                 'video': video},
                request=request)
        }
        data = json.dumps(some_data_to_dump)
        return HttpResponse(data, content_type='application/json')
    return render(
        request,
        'video_completion.html',
        {'video': video,
         'list_document': list_document,
         'list_track': list_track,
         'list_overlay': list_overlay})


@csrf_protect
def video_completion_document(request, slug):
    if not request.user.is_authenticated() or not request.user.is_staff:
        return HttpResponseForbidden()
    video = get_object_or_404(Video, slug=slug)
    if request.user != video.owner.user and not request.user.is_superuser:
        messages.add_message(
            request, messages.ERROR, _(u'You cannot complement this video.'))
        return HttpResponseForbidden()

    list_contributor = video.contributor_set.all()
    list_document = video.document_set.all()
    list_track = video.track_set.all()
    list_overlay = video.overlay_set.all()

    if request.POST and request.POST.get('action'):
        try:
            func = getattr(
                'pod.filepicker.views',
                'video_completion_document_{0}'.format(request.POST['action']))
        except AttributeError:
            return HttpResponseBadRequest()
        else:
            return func(request, video)
    else:
        return render(
            request,
            'video_completion.html',
            {'video': video,
             'list_contributor': list_contributor,
             'list_document': list_document,
             'list_track': list_track,
             'list_overlay': list_overlay})


def video_completion_document_new(request, video):
    list_contributor = video.contributor_set.all()
    list_document = video.document_set.all()
    list_track = video.track_set.all()
    list_overlay = video.overlay_set.all()

    form_document = DocumentForm(initial={'video': video})
    if request.is_ajax():
        return render(
            request,
            'document/form_document.html',
            {'form_document': form_document,
             'video': video})
    else:
        return render(
            request,
            'video_completion.html',
            {'video': video,
             'list_contributor': list_contributor,
             'list_document': list_document,
             'form_document': form_document,
             'list_track': list_track,
             'list_overlay': list_overlay})


def video_completion_document_save(request, video):
    list_contributor = video.contributor_set.all()
    list_document = video.document_set.all()
    list_track = video.track_set.all()
    list_overlay = video.overlay_set.all()

    form_document = DocumentForm(request.POST)
    if (request.POST.get('document_id') and
            request.POST['document_id'] != 'None'):
        document = get_object_or_404(
            Document, id=request.POST['document_id'])
        form_document = DocumentForm(
            request.POST, instance=document)
    else:
        form_document = DocumentForm(request.POST)
    if form_document.is_valid():
        form_document.save()
        list_document = video.document_set.all()
        if request.is_ajax():
            some_data_to_dump = {
                'list_data': render_to_string(
                    'document/list_document.html',
                    {'list_document': list_document,
                     'video': video},
                    request=request)
            }
            data = json.dumps(some_data_to_dump)
            return HttpResponse(
                data,
                content_type='application/json')
        else:
            return render(
                request,
                'video_completion.html',
                {'video': video,
                 'list_contributor': list_contributor,
                 'list_document': list_document,
                 'list_track': list_track,
                 'list_overlay': list_overlay})
    else:
        if request.is_ajax():
            some_data_to_dump = {
                'errors': '{0}'.format(_('Please correct errors')),
                'form': render_to_string(
                    'document/form_document.html',
                    {'video': video,
                     'form_document': form_document},
                    request=request)
            }
            data = json.dumps(some_data_to_dump)
            return HttpResponse(
                data,
                content_type='application/json')
        else:
            return render(
                request,
                'video_completion.html',
                {'video': video,
                 'list_contributor': list_contributor,
                 'list_document': list_document,
                 'list_track': list_track,
                 'list_overlay': list_overlay})


def video_completion_document_modify(request, video):
    list_contributor = video.contributor_set.all()
    list_document = video.document_set.all()
    list_track = video.track_set.all()
    list_overlay = video.overlay_set.all()

    document = get_object_or_404(Document, id=request.POST['id'])
    form_document = DocumentForm(instance=document)
    if request.is_ajax():
        return render(
            request,
            'document/form_document.html',
            {'form_document': form_document,
             'video': video})
    else:
        return render(
            request,
            'video_completion.html',
            {'video': video,
             'list_contributor': list_contributor,
             'list_document': list_document,
             'form_document': form_document,
             'list_track': list_track,
             'list_overlay': list_overlay})


def video_completion_document_delete(request, video):
    list_contributor = video.contributor_set.all()
    list_document = video.document_set.all()
    list_track = video.track_set.all()
    list_overlay = video.overlay_set.all()

    document = get_object_or_404(Document, id=request.POST['id'])
    document.delete()
    list_document = video.document_set.all()
    if request.is_ajax():
        some_data_to_dump = {
            'list_data': render_to_string(
                'document/list_document.html',
                {'list_document': list_document,
                 'video': video},
                request=request)
        }
        data = json.dumps(some_data_to_dump)
        return HttpResponse(data, content_type='application/json')
    else:
        return render(
            request,
            'video_completion.html',
            {'video': video,
             'list_contributor': list_contributor,
             'list_document': list_document,
             'list_track': list_track,
             'list_overlay': list_overlay})


@csrf_protect
def video_completion_track(request, slug):
    if not request.user.is_authenticated() or not request.user.is_staff:
        return HttpResponseForbidden()
    video = get_object_or_404(Video, slug=slug)
    if request.user != video.owner.user and not request.user.is_superuser:
        messages.add_message(
            request, messages.ERROR, _(u'You cannot complement this video.'))
        return HttpResponseForbidden()

    list_contributor = video.contributor_set.all()
    list_track = video.track_set.all()
    list_document = video.document_set.all()
    list_overlay = video.overlay_set.all()

    if request.POST and request.POST.get('action'):
        try:
            func = getattr(
                'pod.filepicker.views',
                'video_completion_track_{0}'.format(request.POST['action']))
        except AttributeError:
            return HttpResponseBadRequest()
        else:
            return func(request, video)
    else:
        return render(
            request,
            'video_completion.html',
            {'video': video,
             'list_contributor': list_contributor,
             'list_document': list_document,
             'list_track': list_track,
             'list_overlay': list_overlay})


def video_completion_track_new(request, video):
    list_contributor = video.contributor_set.all()
    list_track = video.track_set.all()
    list_document = video.document_set.all()
    list_overlay = video.overlay_set.all()

    form_track = TrackForm(initial={'video': video})
    if request.is_ajax():
        return render(
            request,
            'track/form_track.html',
            {'form_track': form_track,
             'video': video})
    else:
        return render(
            request,
            'video_completion.html',
            {'video': video,
             'list_contributor': list_contributor,
             'list_document': list_document,
             'list_track': list_track,
             'form_track': form_track,
             'list_overlay': list_overlay})


def video_completion_track_save(request, video):
    list_contributor = video.contributor_set.all()
    list_track = video.track_set.all()
    list_document = video.document_set.all()
    list_overlay = video.overlay_set.all()

    form_track = TrackForm(request.POST)
    if request.POST.get('track_id') and request.POST['track_id'] != 'None':
        track = get_object_or_404(Track, id=request.POST['track_id'])
        form_track = TrackForm(request.POST, instance=track)
    else:
        form_track = TrackForm(request.POST)
    if form_track.is_valid():
        form_track.save()
        list_track = video.track_set.all()
        if request.is_ajax():
            some_data_to_dump = {'list_data': render_to_string(
                'track/list_track.html',
                {'list_track': list_track,
                 'video': video},
                request=request)
            }
            data = json.dumps(some_data_to_dump)
            return HttpResponse(data, content_type='application/json')
        else:
            return render(
                request,
                'video_completion.html',
                {'video': video,
                 'list_contributor': list_contributor,
                 'list_document': list_document,
                 'list_track': list_track,
                 'list_overlay': list_overlay})
    else:
        if request.is_ajax():
            some_data_to_dump = {
                'errors': '{0}'.format('Please correct errors'),
                'form': render_to_string(
                    'track/form_track.html',
                    {'video': video,
                     'form_track': form_track},
                    request=request)
            }
            data = json.dumps(some_data_to_dump)
            return HttpResponse(data, content_type='application/json')
        else:
            return render(
                request,
                'video_completion.html',
                {'video': video,
                 'list_contributor': list_contributor,
                 'list_document': list_document,
                 'list_track': list_track,
                 'form_track': form_track,
                 'list_overlay': list_overlay})


def video_completion_track_modify(request, video):
    list_contributor = video.contributor_set.all()
    list_track = video.track_set.all()
    list_document = video.document_set.all()
    list_overlay = video.overlay_set.all()

    track = get_object_or_404(Track, id=request.POST['id'])
    form_track = TrackForm(instance=track)
    if request.is_ajax():
        return render(
            request,
            'track/form_track.html',
            {'form_track': form_track,
             'video': video})
    else:
        return render(
            request,
            'video_completion.html',
            {'video': video,
             'list_contributor': list_contributor,
             'list_document': list_document,
             'list_track': list_track,
             'form_track': form_track,
             'list_overlay': list_overlay})


def video_completion_track_delete(request, video):
    list_contributor = video.contributor_set.all()
    list_track = video.track_set.all()
    list_document = video.document_set.all()
    list_overlay = video.overlay_set.all()

    track = get_object_or_404(Track, id=request.POST['id'])
    track.delete()
    list_track = video.track_set.all()
    if request.is_ajax():
        some_data_to_dump = {
            'list_data': render_to_string(
                'track/list_track.html',
                {'list_track': list_track,
                 'video': video},
                request=request)
        }
        data = json.dumps(some_data_to_dump)
        return HttpResponse(data, content_type='application/json')
    else:
        return render(
            request,
            'video_completion.html',
            {'video': video,
             'list_contributor': list_contributor,
             'list_document': list_document,
             'list_track': list_track,
             'list_overlay': list_overlay})


@csrf_protect
def video_completion_overlay(request, slug):
    if not request.user.is_authenticated() or not request.user.is_staff:
        return HttpResponseForbidden()
    video = get_object_or_404(Video, slug=slug)
    if request.user != video.owner.user and not request.user.is_superuser:
        messages.add_message(
            request, messages.ERROR, _(u'You cannot complement this video.'))
        return HttpResponseForbidden()

    list_contributor = video.contributor_set.all()
    list_document = video.document_set.all()
    list_track = video.track_set.all()
    list_overlay = video.overlay_set.all()

    if request.POST and request.POST.get('action'):
        try:
            func = getattr(
                'pod.filepicker.views',
                'video_completion_overlay_{0}'.format(request.POST['action']))
        except AttributeError:
            return HttpResponseBadRequest()
        else:
            return func(request, video)
    else:
        return render(
            request,
            'video_completion.html',
            {'video': video,
             'list_contributor': list_contributor,
             'list_document': list_document,
             'list_track': list_track,
             'list_overlay': list_overlay})


def video_completion_overlay_new(request, video):
    list_contributor = video.contributor_set.all()
    list_document = video.document_set.all()
    list_track = video.track_set.all()
    list_overlay = video.overlay_set.all()

    form_overlay = OverlayForm(initial={'video': video})
    if request.is_ajax():
        return render(
            request,
            'overlay/form_overlay.html',
            {'form_overlay': form_overlay,
             'video': video})
    return render(
        request,
        'video_completion.html',
        {'video': video,
         'list_contributor': list_contributor,
         'list_document': list_document,
         'list_track': list_track,
         'list_overlay': list_overlay,
         'form_overlay': form_overlay})


def video_completion_overlay_save(request, video):
    list_contributor = video.contributor_set.all()
    list_document = video.document_set.all()
    list_track = video.track_set.all()
    list_overlay = video.overlay_set.all()

    form_overlay = OverlayForm(request.POST)
    if (request.POST.get('overlay_id') and
            request.POST['overlay_id'] != 'None'):
        overlay = get_object_or_404(
            Overlay, id=request.POST['overlay_id'])
        form_overlay = OverlayForm(
            request.POST, instance=overlay)
    else:
        form_overlay = OverlayForm(request.POST)
    if form_overlay.is_valid():
        form_overlay.save()
        list_overlay = video.overlay_set.all()
        if request.is_ajax():
            some_data_to_dump = {
                'list_data': render_to_string(
                    'overlay/list_overlay.html',
                    {'list_overlay': list_overlay,
                     'video': video},
                    request=request)
            }
            data = json.dumps(some_data_to_dump)
            return HttpResponse(data, content_type='application/json')
        return render(
            request,
            'video_completion.html',
            {'video': video,
             'list_contributor': list_contributor,
             'list_document': list_document,
             'list_track': list_track,
             'list_overlay': list_overlay})
    else:
        if request.is_ajax():
            some_data_to_dump = {
                'errors': '{0}'.format(_('Please correct errors')),
                'form': render_to_string(
                    'overlay/form_overlay.html',
                    {'video': video,
                     'form_overlay': form_overlay},
                    request=request)
            }
            data = json.dumps(some_data_to_dump)
            return HttpResponse(data, content_type='application/json')
        return render(
            request,
            'video_completion.html',
            {'video': video,
             'list_contributor': list_contributor,
             'list_document': list_document,
             'list_track': list_track,
             'list_overlay': list_overlay,
             'form_overlay': form_overlay})


def video_completion_overlay_modify(request, video):
    list_contributor = video.contributor_set.all()
    list_document = video.document_set.all()
    list_track = video.track_set.all()
    list_overlay = video.overlay_set.all()

    overlay = get_object_or_404(Overlay, id=request.POST['id'])
    form_overlay = OverlayForm(instance=overlay)
    if request.is_ajax():
        return render(
            request,
            'overlay/form_overlay.html',
            {'form_overlay': form_overlay,
             'video': video})
    return render(
        request,
        'video_completion.html',
        {'video': video,
         'list_contributor': list_contributor,
         'list_document': list_document,
         'list_track': list_track,
         'list_overlay': list_overlay,
         'form_overlay': form_overlay})


def video_completion_overlay_delete(request, video):
    list_contributor = video.contributor_set.all()
    list_document = video.document_set.all()
    list_track = video.track_set.all()
    list_overlay = video.overlay_set.all()

    overlay = get_object_or_404(Overlay, id=request.POST['id'])
    overlay.delete()
    list_overlay = video.overlay_set.all()
    if request.is_ajax():
        some_data_to_dump = {
            'list_data': render_to_string(
                'overlay/list_overlay.html',
                {'list_overlay': list_overlay,
                 'video': video},
                request=request)
        }
        data = json.dumps(some_data_to_dump)
        return HttpResponse(data, content_type='application/json')
    else:
        return render(
            request,
            'video_completion.html',
            {'video': video,
             'list_contributor': list_contributor,
             'list_document': list_document,
             'list_track': list_track,
             'list_overlay': list_overlay})
