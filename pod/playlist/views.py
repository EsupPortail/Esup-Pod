from django.contrib.auth.decorators import login_required


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