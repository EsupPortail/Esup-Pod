from django.core.paginator import Paginator
from django.core.paginator import EmptyPage
from django.core.paginator import PageNotAnInteger
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.shortcuts import get_object_or_404
from django.utils.translation import ugettext_lazy as _
from django.views.decorators.csrf import csrf_protect
from pod.playlist.models import Playlist
from pod.playlist.forms import PlaylistForm


@login_required(redirect_field_name='referrer')
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

    if request.is_ajax():
        return render(
            request,
            'playlist_list.html',
            {'playlists': playlists, 'full_path': full_path}
        )
    return render(
        request,
        'my_playlists.html',
        {'playlists': playlists, 'full_path': full_path}
    )


@login_required
@csrf_protect
def playlist(request, slug=None):
    playlist = get_object_or_404(Playlist, slug=slug) if slug else None
    list_videos = playlist.playlistelement_set.all()
    if (playlist and
            request.user != playlist.owner and not request.user.is_superuser):
        messages.add_message(
            request, messages.ERROR, _('You cannot edit this video.'))
        raise PermissionDenied

    form = PlaylistForm(instance=playlist, initial={'owner': request.user})

    if request.POST:
        form = PlaylistForm(request.POST, instance=playlist)
        if form.is_valid():
            playlist = form.save()
            messages.add_message(
                request, messages.INFO, _('The changes have been saved.'))
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
