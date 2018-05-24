from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.shortcuts import get_object_or_404
from django.shortcuts import render
from django.http import HttpResponse
from django.core.exceptions import SuspiciousOperation
from django.core.exceptions import PermissionDenied
from django.views.decorators.csrf import csrf_protect
from django.contrib import messages
from django.utils.translation import ugettext_lazy as _
from django.contrib.auth.decorators import login_required
from django.db.models import Count

from pod.video.models import Video
from pod.video.models import Channel
from pod.video.models import Theme
from tagging.models import TaggedItem

from pod.video.forms import VideoForm
from pod.video.forms import ChannelForm
from pod.video.forms import FrontThemeForm

# Create your views here.
VIDEOS = Video.objects.filter(encoding_in_progress=False, is_draft=False)


def channel(request, slug_c, slug_t=None):
    channel = get_object_or_404(Channel, slug=slug_c)

    videos_list = VIDEOS.filter(channel=channel)

    theme = None
    if slug_t:
        theme = get_object_or_404(Theme, slug=slug_t)
        list_theme = theme.get_all_children_flat()
        videos_list = videos_list.filter(theme__in=list_theme)

    page = request.GET.get('page', 1)
    full_path = ""
    if page:
        full_path = request.get_full_path().replace(
            "?page=%s" % page, "").replace("&page=%s" % page, "")
    paginator = Paginator(videos_list, 12)
    try:
        videos = paginator.page(page)
    except PageNotAnInteger:
        videos = paginator.page(1)
    except EmptyPage:
        videos = paginator.page(paginator.num_pages)

    if request.is_ajax():
        return render(
            request, 'videos/video_list.html',
            {'videos': videos, "full_path": full_path})

    return render(request, 'channel/channel.html',
                  {'channel': channel,
                   'videos': videos,
                   'theme': theme,
                   'full_path': full_path})


@login_required(redirect_field_name='referrer')
def my_channels(request):
    channels = request.user.owners_channels.all().annotate(
        video_count=Count("video", distinct=True))
    return render(request, 'channel/my_channels.html', {'channels': channels})


@csrf_protect
@login_required(redirect_field_name='referrer')
def channel_edit(request, slug):
    channel = get_object_or_404(Channel, slug=slug)
    if (request.user not in channel.owners.all()
            and not request.user.is_superuser):
        messages.add_message(
            request, messages.ERROR, _(u'You cannot edit this channel.'))
        raise PermissionDenied
    channel_form = ChannelForm(
        instance=channel,
        is_staff=request.user.is_staff,
        is_superuser=request.user.is_superuser)
    if request.POST:
        channel_form = ChannelForm(
            request.POST,
            instance=channel,
            is_staff=request.user.is_staff,
            is_superuser=request.user.is_superuser
        )
        if channel_form.is_valid():
            channel = channel_form.save()
            messages.add_message(
                request, messages.INFO,
                _('The changes have been saved.')
            )
        else:
            messages.add_message(
                request, messages.ERROR,
                _(u'One or more errors have been found in the form.'))
    return render(request, 'channel/channel_edit.html', {'form': channel_form})


@csrf_protect
@login_required(redirect_field_name='referrer')
def theme_edit(request, slug):
    channel = get_object_or_404(Channel, slug=slug)
    if (request.user not in channel.owners.all()
            and not request.user.is_superuser):
        messages.add_message(
            request, messages.ERROR, _(u'You cannot edit this channel.'))
        raise PermissionDenied

    if request.POST and request.is_ajax():
        form_theme = FrontThemeForm(initial={"channel": channel})
        return render(request, "channel/form_theme.html",
                                  {'form_theme': form_theme,
                                   'channel': channel}
                                  )
    form_theme = FrontThemeForm(initial={"channel": channel})
    return render(request, 'channel/theme_edit.html', {'channel': channel, 'form_theme':form_theme})


@login_required(redirect_field_name='referrer')
def my_videos(request):
    videos_list = request.user.video_set.all()
    page = request.GET.get('page', 1)

    full_path = ""
    if page:
        full_path = request.get_full_path().replace(
            "?page=%s" % page, "").replace("&page=%s" % page, "")

    paginator = Paginator(videos_list, 12)
    try:
        videos = paginator.page(page)
    except PageNotAnInteger:
        videos = paginator.page(1)
    except EmptyPage:
        videos = paginator.page(paginator.num_pages)

    if request.is_ajax():
        return render(
            request, 'videos/video_list.html',
            {'videos': videos, "full_path": full_path})

    return render(request, 'videos/my_videos.html', {
        'videos': videos, "full_path": full_path
    })


def get_videos_list(request):
    videos_list = VIDEOS

    if request.GET.getlist('type'):
        videos_list = videos_list.filter(
            type__slug__in=request.GET.getlist('type'))
    if request.GET.getlist('discipline'):
        videos_list = videos_list.filter(
            discipline__slug__in=request.GET.getlist('discipline'))
    if request.GET.getlist('owner'):
        videos_list = videos_list.filter(
            owner__username__in=request.GET.getlist('owner'))
    if request.GET.getlist('tag'):
        videos_list = TaggedItem.objects.get_union_by_model(
            videos_list,
            request.GET.getlist('tag'))
    return videos_list


def videos(request):
    videos_list = get_videos_list(request)

    page = request.GET.get('page', 1)
    full_path = ""
    if page:
        full_path = request.get_full_path().replace(
            "?page=%s" % page, "").replace("&page=%s" % page, "")

    paginator = Paginator(videos_list, 12)
    try:
        videos = paginator.page(page)
    except PageNotAnInteger:
        videos = paginator.page(1)
    except EmptyPage:
        videos = paginator.page(paginator.num_pages)

    if request.is_ajax():
        return render(
            request, 'videos/video_list.html',
            {'videos': videos, "full_path": full_path})

    return render(request, 'videos/videos.html', {
        'videos': videos,
        "types": request.GET.getlist('type'),
        "owners": request.GET.getlist('owner'),
        "disciplines": request.GET.getlist('discipline'),
        "tags_slug": request.GET.getlist('tag'),
        "full_path": full_path
    })


def is_in_video_groups(user, video):
    return user.groups.filter(
        name__in=[
            name[0]
            for name in video.restrict_access_to_groups.values_list('name')
        ]
    ).exists()


@csrf_protect
def video(request, slug, slug_c=None, slug_t=None):
    try:
        id = int(slug[:slug.find("-")])
    except ValueError:
        raise SuspiciousOperation('Invalid video id')
    video = get_object_or_404(Video, id=id)

    channel = get_object_or_404(Channel, slug=slug_c) if slug_c else None
    theme = get_object_or_404(Theme, slug=slug_t) if slug_t else None

    is_draft = video.is_draft
    is_restricted = video.is_restricted
    is_restricted_to_group = video.restrict_access_to_groups.all().exists()
    is_password_protected = (video.password is not None)

    is_access_protected = (
        is_draft
        or is_restricted
        or is_restricted_to_group
        or is_password_protected
    )

    if is_access_protected:

        access_granted_for_draft = request.user.is_authenticated() and (
            request.user == video.owner or request.user.is_superuser)
        access_granted_for_restricted = (
            request.user.is_authenticated() and not is_restricted_to_group)
        access_granted_for_group = (
            request.user.is_authenticated()
            and is_in_video_groups(request.user, video)
        )

        show_page = (
            (is_draft and access_granted_for_draft)
            or (
                is_restricted
                and access_granted_for_restricted
                and is_password_protected is False)
            or (
                is_restricted_to_group
                and access_granted_for_group
                and is_password_protected is False)
            or (
                is_password_protected
                and access_granted_for_draft
            )
            or (
                is_password_protected
                and request.POST.password == video.password
            )
        )
        if show_page:
            return render(
                request, 'videos/video.html', {
                    'channel': channel,
                    'video': video,
                    'theme': theme,
                }
            )
        else:
            if is_password_protected:
                return HttpResponse("show form password")
            elif request.user.is_authenticated():
                messages.add_message(
                    request, messages.ERROR,
                    _(u'You cannot watch this video.'))
                raise PermissionDenied
            else:
                return HttpResponse("redirect to login page")
    else:
        return render(
            request, 'videos/video.html', {
                'channel': channel,
                'video': video,
                'theme': theme,
            }
        )


@csrf_protect
@login_required(redirect_field_name='referrer')
def video_edit(request, slug=None):

    video = get_object_or_404(Video, slug=slug) if slug else None

    if video and request.user != video.owner and not request.user.is_superuser:
        messages.add_message(
            request, messages.ERROR, _(u'You cannot edit this video.'))
        raise PermissionDenied

    form = VideoForm(
        instance=video,
        is_staff=request.user.is_staff,
        is_superuser=request.user.is_superuser,
        current_user=request.user
    )

    if request.method == 'POST':
        form = VideoForm(
            request.POST,
            request.FILES,
            instance=video,
            is_staff=request.user.is_staff,
            is_superuser=request.user.is_superuser,
            current_user=request.user
        )
        if form.is_valid():
            video = form.save(commit=False)
            if request.POST.get('owner') and request.POST.get('owner') != "":
                video.owner = form.cleaned_data['owner']
            else:
                video.owner = request.user
            video.save()
            messages.add_message(
                request, messages.INFO,
                _('The changes have been saved.')
            )
        else:
            messages.add_message(
                request, messages.ERROR,
                _(u'One or more errors have been found in the form.'))

    return render(request, 'videos/video_edit.html', {
        'form': form}
    )
