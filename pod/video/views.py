from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.shortcuts import get_object_or_404
from django.shortcuts import render
from django.http import HttpResponse, HttpResponseNotFound, JsonResponse
from django.core.exceptions import SuspiciousOperation
from django.core.exceptions import PermissionDenied
from django.views.decorators.csrf import csrf_protect
from django.contrib import messages
from django.utils.translation import ugettext_lazy as _
from django.contrib.sites.shortcuts import get_current_site
from django.contrib.auth.decorators import login_required
from django.db.models import Count, F
from django.template.loader import render_to_string
from django.conf import settings
from django.shortcuts import redirect
from django.urls import reverse

from pod.video.models import Video
from pod.video.models import Channel
from pod.video.models import Theme
from pod.video.models import Notes
from pod.video.models import ViewCount
from tagging.models import TaggedItem

from pod.video.forms import VideoForm
from pod.video.forms import ChannelForm
from pod.video.forms import FrontThemeForm
from pod.video.forms import VideoPasswordForm
from pod.video.forms import VideoDeleteForm
from pod.video.forms import NotesForm

import json
import re
from datetime import date

from pod.playlist.models import Playlist
from django.db import transaction
from django.db import IntegrityError

VIDEOS = Video.objects.filter(encoding_in_progress=False, is_draft=False)
RESTRICT_EDIT_VIDEO_ACCESS_TO_STAFF_ONLY = getattr(
    settings, 'RESTRICT_EDIT_VIDEO_ACCESS_TO_STAFF_ONLY', False)
THEME_ACTION = ['new', 'modify', 'delete', 'save']

TEMPLATE_VISIBLE_SETTINGS = getattr(
    settings,
    'TEMPLATE_VISIBLE_SETTINGS',
    {
        'TITLE_SITE': 'Pod',
        'TITLE_ETB': 'University name',
        'LOGO_SITE': 'img/logoPod.svg',
        'LOGO_ETB': 'img/logo_etb.svg',
        'LOGO_PLAYER': 'img/logoPod.svg',
        'LINK_PLAYER': '',
        'FOOTER_TEXT': ('',),
        'FAVICON': 'img/logoPod.svg',
        'CSS_OVERRIDE': ''
    }
)

TITLE_ETB = TEMPLATE_VISIBLE_SETTINGS[
    'TITLE_ETB'] if (
        TEMPLATE_VISIBLE_SETTINGS.get('TITLE_ETB')
) else 'University'

# ############################################################################
# CHANNEL
# ############################################################################


def channel(request, slug_c, slug_t=None):
    channel = get_object_or_404(Channel, slug=slug_c)

    videos_list = VIDEOS.filter(channel=channel)

    theme = None
    if slug_t:
        theme = get_object_or_404(Theme, channel=channel, slug=slug_t)
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


# ############################################################################
# THEME EDIT
# ############################################################################


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
        if request.POST['action'] in THEME_ACTION:
            return eval(
                'theme_edit_{0}(request, channel)'.format(
                    request.POST['action'])
            )

    form_theme = FrontThemeForm(initial={"channel": channel})
    return render(request,
                  'channel/theme_edit.html',
                  {'channel': channel,
                   'form_theme': form_theme})


def theme_edit_new(request, channel):
    form_theme = FrontThemeForm(initial={"channel": channel})
    return render(request, "channel/form_theme.html",
                  {'form_theme': form_theme,
                   'channel': channel}
                  )


def theme_edit_modify(request, channel):
    theme = get_object_or_404(Theme, id=request.POST['id'])
    form_theme = FrontThemeForm(instance=theme)
    return render(request, "channel/form_theme.html",
                  {'form_theme': form_theme,
                   'channel': channel}
                  )


def theme_edit_delete(request, channel):
    theme = get_object_or_404(Theme, id=request.POST['id'])
    theme.delete()
    rendered = render_to_string("channel/list_theme.html",
                                {'list_theme': channel.themes.all(),
                                 'channel': channel}, request)
    list_element = {
        'list_element': rendered
    }
    data = json.dumps(list_element)
    return HttpResponse(data, content_type='application/json')


def theme_edit_save(request, channel):
    form_theme = None

    if (request.POST.get("theme_id")
            and request.POST.get("theme_id") != "None"):
        theme = get_object_or_404(Theme, id=request.POST['theme_id'])
        form_theme = FrontThemeForm(request.POST, instance=theme)
    else:
        form_theme = FrontThemeForm(request.POST)

    if form_theme.is_valid():
        form_theme.save()
        rendered = render_to_string("channel/list_theme.html",
                                    {'list_theme': channel.themes.all(),
                                     'channel': channel}, request)
        list_element = {
            'list_element': rendered
        }
        data = json.dumps(list_element)
        return HttpResponse(data, content_type='application/json')
    else:
        rendered = render_to_string("channel/form_theme.html",
                                    {'form_theme': form_theme,
                                     'channel': channel}, request)
        some_data_to_dump = {
            'errors': "%s" % _('Please correct errors'),
            'form': rendered
        }
        data = json.dumps(some_data_to_dump)
        return HttpResponse(data, content_type='application/json')


# ############################################################################
# VIDEOS
# ############################################################################


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
    return videos_list.distinct()


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


def get_note_form(request, video):
    notesForm = None
    if request.user.is_authenticated:
        note = None
        if Notes.objects.filter(user=request.user, video=video).exists():
            note = Notes.objects.get(user=request.user, video=video)
        notesForm = NotesForm(instance=note)
    return notesForm


def get_video_access(request, video, slug_private):
    is_draft = video.is_draft
    is_restricted = video.is_restricted
    is_restricted_to_group = video.restrict_access_to_groups.all().exists()
    """
    is_password_protected = (video.password is not None
                             and video.password != '')
    """
    is_access_protected = (
        is_draft
        or is_restricted
        or is_restricted_to_group
        # or is_password_protected
    )

    if is_access_protected:
        access_granted_for_private = (
            slug_private and slug_private == video.get_hashkey()
        )
        access_granted_for_draft = request.user.is_authenticated() and (
            request.user == video.owner or request.user.is_superuser)
        access_granted_for_restricted = (
            request.user.is_authenticated() and not is_restricted_to_group)
        access_granted_for_group = (
            request.user.is_authenticated()
            and is_in_video_groups(request.user, video)
        ) or request.user == video.owner or request.user.is_superuser

        show_page = (
            access_granted_for_private
            or
            (is_draft and access_granted_for_draft)
            or (
                is_restricted
                and access_granted_for_restricted)
            # and is_password_protected is False)
            or (
                is_restricted_to_group
                and access_granted_for_group)
            # and is_password_protected is False)
            # or (
            #     is_password_protected
            #     and access_granted_for_draft
            # )
            # or (
            #     is_password_protected
            #     and request.POST.get('password')
            #     and request.POST.get('password') == video.password
            # )
        )
        if show_page:
            return True
        else:
            return False
    else:
        return True


@csrf_protect
def video(request, slug, slug_c=None, slug_t=None, slug_private=None):
    template_video = 'videos/video-iframe.html' if (
        request.GET.get('is_iframe')) else 'videos/video.html'
    return render_video(request, slug, slug_c, slug_t, slug_private,
                        template_video, None)


def render_video(request, slug, slug_c=None, slug_t=None, slug_private=None,
                 template_video='videos/video.html', more_data=None):
    try:
        id = int(slug[:slug.find("-")])
    except ValueError:
        raise SuspiciousOperation('Invalid video id')
    video = get_object_or_404(Video, id=id)
    notesForm = get_note_form(request, video)
    channel = get_object_or_404(Channel, slug=slug_c) if slug_c else None
    theme = get_object_or_404(
        Theme, channel=channel, slug=slug_t) if slug_t else None
    playlist = get_object_or_404(
        Playlist,
        slug=request.GET['playlist']) if request.GET.get('playlist') else None

    is_password_protected = (
        video.password is not None and video.password != '')

    show_page = get_video_access(request, video, slug_private)

    if ((show_page and not is_password_protected) or (
        show_page and is_password_protected
        and request.POST.get('password')
        and request.POST.get('password') == video.password
    ) or (
        slug_private and slug_private == video.get_hashkey()
    ) or request.user == video.owner or request.user.is_superuser):
        return render(
            request, template_video, {
                'channel': channel,
                'video': video,
                'theme': theme,
                'notesForm': notesForm,
                'playlist': playlist,
                'more_data': more_data
            }
        )
    else:
        is_draft = video.is_draft
        is_restricted = video.is_restricted
        is_restricted_to_group = video.restrict_access_to_groups.all(
        ).exists()
        is_access_protected = (
            is_draft
            or is_restricted
            or is_restricted_to_group
        )
        if is_password_protected and (
            not is_access_protected or (
                is_access_protected and show_page)):
            form = VideoPasswordForm(
                request.POST) if request.POST else VideoPasswordForm()
            if (request.POST.get('password')
                    and request.POST.get('password') != video.password):
                messages.add_message(
                    request, messages.ERROR,
                    _('The password is incorrect.'))
            return render(
                request, 'videos/video.html', {
                    'channel': channel,
                    'video': video,
                    'theme': theme,
                    'form': form,
                    'notesForm': notesForm,
                    'playlist': playlist,
                    'more_data': more_data
                }
            )
        elif request.user.is_authenticated():
            messages.add_message(
                request, messages.ERROR,
                _('You cannot watch this video.'))
            raise PermissionDenied
        else:
            iframe_param = 'is_iframe=true&' if (
                request.GET.get('is_iframe')) else ''
            return redirect(
                '%s?%sreferrer=%s' % (
                    settings.LOGIN_URL,
                    iframe_param,
                    request.get_full_path())
            )


@csrf_protect
@login_required(redirect_field_name='referrer')
def video_edit(request, slug=None):

    video = get_object_or_404(Video, slug=slug) if slug else None

    if (RESTRICT_EDIT_VIDEO_ACCESS_TO_STAFF_ONLY
            and request.user.is_staff is False):
        return render(request,
                      'videos/video_edit.html',
                      {'access_not_allowed': True}
                      )

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
            form.save_m2m()
            messages.add_message(
                request, messages.INFO,
                _('The changes have been saved.')
            )
            if request.POST.get('_saveandsee'):
                return redirect(
                    reverse('video', args=(video.slug,))
                )
            else:
                return redirect(
                    reverse('video_edit', args=(video.slug,))
                )
        else:
            messages.add_message(
                request, messages.ERROR,
                _(u'One or more errors have been found in the form.'))

    return render(request, 'videos/video_edit.html', {
        'form': form}
    )


@csrf_protect
@login_required(redirect_field_name='referrer')
def video_delete(request, slug=None):

    video = get_object_or_404(Video, slug=slug)

    if request.user != video.owner and not request.user.is_superuser:
        messages.add_message(
            request, messages.ERROR, _(u'You cannot delete this video.'))
        raise PermissionDenied

    form = VideoDeleteForm()

    if request.method == "POST":
        form = VideoDeleteForm(request.POST)
        if form.is_valid():
            video.delete()
            messages.add_message(
                request, messages.INFO, _('The video has been deleted.'))
            return redirect(
                reverse('my_videos')
            )
        else:
            messages.add_message(
                request, messages.ERROR,
                _(u'One or more errors have been found in the form.'))

    return render(request, 'videos/video_delete.html', {
        'video': video,
        'form': form}
    )


@csrf_protect
@login_required(redirect_field_name='referrer')
def video_notes(request, slug):
    video = get_object_or_404(Video, slug=slug)
    notesForm = NotesForm()

    if request.method == "POST":
        notesForm = NotesForm(request.POST)
        if notesForm.is_valid():
            note, created = Notes.objects.get_or_create(
                user=request.user, video=video)
            note.note = notesForm.cleaned_data["note"]
            note.save()
            messages.add_message(
                request, messages.INFO, _('The note has been saved.'))
        else:
            messages.add_message(
                request, messages.ERROR,
                _(u'One or more errors have been found in the form.'))

    return render(request, 'videos/video_notes.html', {
        'video': video,
        'notesForm': notesForm}
    )


# @csrf_protect
# def video_count(request, id):
#     video = get_object_or_404(Video, id=id)
#     if request.method == "POST":
#         try:
#             viewCount = ViewCount.objects.get(video=video, date=date.today())
#             viewCount.count = F('count')+1
#             viewCount.save(update_fields=['count'])
#         except ViewCount.DoesNotExist:
#             ViewCount.objects.create(video=video, count=1)
#         return HttpResponse("ok")
#     messages.add_message(
#         request, messages.ERROR, _(u'You cannot access to this view.'))
#     raise PermissionDenied
@csrf_protect
def video_count(request, id):
    video = get_object_or_404(Video, id=id)
    if request.method == "POST":
        try:
            viewCount = ViewCount.objects.get(video=video, date=date.today())
        except ViewCount.DoesNotExist:
            try:
                with transaction.atomic():
                    ViewCount.objects.create(video=video, count=1)
                    return HttpResponse("ok")
            except IntegrityError:
                viewCount = ViewCount.objects.get(video=video,
                                                  date=date.today())
        viewCount.count = F('count')+1
        viewCount.save(update_fields=['count'])
        return HttpResponse("ok")
    messages.add_message(
        request, messages.ERROR, _(u'You cannot access to this view.'))
    raise PermissionDenied


def video_oembed(request):
    if not request.GET.get('url'):
        raise SuspiciousOperation('URL must be specified')
    format = "xml" if request.GET.get("format") == "xml" else "json"

    data = {}
    data['type'] = "video"
    data['version'] = "1.0"
    data['provider_name'] = TITLE_ETB
    protocole = "https" if request.is_secure() else "http"
    data['provider_url'] = "%s://%s" % (protocole,
                                        get_current_site(request).domain)
    data['width'] = 640
    data['height'] = 360

    reg = (r'^https?://(.*)/video/(?P<slug>[\-\d\w]+)/'
           + r'(?P<slug_private>[\-\d\w]+)?/?(.*)')
    url = request.GET.get('url')
    p = re.compile(reg)
    m = p.match(url)

    if m:
        video_slug = m.group('slug')
        slug_private = m.group('slug_private')
        try:
            id = int(video_slug[:video_slug.find("-")])
        except ValueError:
            raise SuspiciousOperation('Invalid video id')
        video = get_object_or_404(Video, id=id)

        data['title'] = video.title
        data['author_name'] = video.owner.get_full_name()
        data['author_url'] = "%s%s?owner=%s" % (
            data['provider_url'], reverse('videos'), video.owner.username)
        data['html'] = (
            "<iframe src=\"%(provider)s%(video_url)s%(slug_private)s"
            + "?is_iframe=true\" width=\"640\" height=\"360\" style=\""
            + "padding: 0; margin: 0; border:0\" allowfullscreen ></iframe>"
        ) % {
            'provider': data['provider_url'],
            'video_url': reverse('video', kwargs={'slug': video.slug}),
            'slug_private': "%s/" % slug_private if slug_private else ""
        }
    else:
        return HttpResponseNotFound('<h1>Url not match</h1>')

    if format == "xml":
        xml = """
            <oembed>
                <html>
                    %(html)s
                </html>
                <title>%(title)s</title>
                <provider_name>%(provider_name)s</provider_name>
                <author_url>%(author_url)s</author_url>
                <height>%(height)s</height>
                <provider_url>%(provider_url)s</provider_url>
                <type>video</type>
                <width>%(width)s</width>
                <version>1.0</version>
                <author_name>%(author_name)s</author_name>
            </oembed>
        """ % {
            'html': data['html'].replace('<', '&lt;').replace('>', '&gt;'),
            'title': data['title'],
            'provider_name': data['provider_name'],
            'author_url': data['author_url'],
            'height': data['height'],
            'provider_url': data['provider_url'],
            'width': data['width'],
            'author_name': data['author_name']
        }
        return HttpResponse(xml, content_type='application/xhtml+xml')
        # return HttpResponseNotFound('<h1>XML not implemented</h1>')
    else:
        return JsonResponse(data)
