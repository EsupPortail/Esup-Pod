from django.core.paginator import Paginator
from django.core.paginator import EmptyPage
from django.core.paginator import PageNotAnInteger
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.shortcuts import render
from django.shortcuts import get_object_or_404
from django.template.loader import render_to_string
from django.utils.translation import ugettext_lazy as _
from django.views.decorators.csrf import csrf_protect
from pod.playlist.models import Playlist
from pod.playlist.models import PlaylistElement
from pod.playlist.forms import PlaylistForm

import json


@login_required(redirect_field_name='referrer')
@csrf_protect
def my_playlists(request):
    playlists = request.user.playlist_set.all()
    page = request.GET.get('page', 1)

    full_path = ''
    if page:
        full_path = request.get_full_path().replace(
            '?page={0}'.format(page), '').replace(
            '&page={0}'.format(page), '')
    paginator = Paginator(playlists, 12)
    try:
        playlists = paginator.page(page)
    except PageNotAnInteger:
        playlists = paginator.page(1)
    except EmptyPage:
        playlists = paginator.page(paginator.num_pages)

    if request.POST and request.is_ajax():
        playlist = get_object_or_404(Playlist, id=request.POST['playlist'])
        if playlist.owner == request.user:
            playlist.delete()
            some_data_to_dump = {
                'success': '{0}'.format(_('This playlist has been deleted.'))
            }
        else:
            some_data_to_dump = {
                'fail': '{0}'.format(
                    _('Only the owner of the playlist can delete them.'))
            }
        data = json.dumps(some_data_to_dump)
        return HttpResponse(data, content_type='application/json')
    return render(
        request,
        'my_playlists.html',
        {'playlists': playlists, 'full_path': full_path}
    )


@login_required
@csrf_protect
def playlist(request, slug=None):
    if slug:
        playlist = get_object_or_404(Playlist, slug=slug)
        list_videos = playlist.playlistelement_set.all()
    else:
        playlist = None
        list_videos = None
    if (playlist and
            request.user != playlist.owner and not request.user.is_superuser):
        messages.add_message(
            request, messages.ERROR, _('You cannot edit this playlist.'))
        raise PermissionDenied

    form = PlaylistForm(instance=playlist, initial={'owner': request.user})

    if request.POST:
        if request.is_ajax():
            if request.POST.get('action') == 'move':
                data = json.loads(request.POST['videos'])
                for slug in data:
                    element = get_object_or_404(
                        PlaylistElement, video__slug=slug, playlist=playlist)
                    element.position = data[slug]
                    element.save()
                some_data_to_dump = {
                    'success': '{0}'.format(
                        _('The playlist has been saved !'))
                }
                data = json.dumps(some_data_to_dump)
                return HttpResponse(data, content_type='application/json')
            if request.POST.get('action') == 'delete':
                slug = request.POST['video']
                element = get_object_or_404(
                    PlaylistElement, video__slug=slug)
                element.delete()
                some_data_to_dump = {
                    'success': '{0}'.format(
                        _('This video has been removed from your playlist.'))
                }
                data = json.dumps(some_data_to_dump)
                return HttpResponse(data, content_type='application/json')

        form = PlaylistForm(request.POST, instance=playlist)
        if form.is_valid():
            playlist = form.save()
            messages.add_message(
                request, messages.INFO, _('The playlist have been saved.'))
        else:
            messages.add_message(
                request,
                messages.ERROR,
                _('One or more errors have been found in the form.'))

    return render(
        request,
        'playlist.html',
        {'form': form, 'list_videos': list_videos}
    )
