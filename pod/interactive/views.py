from django.shortcuts import render
from django.conf import settings
from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404
from django.shortcuts import redirect
from django.utils.translation import ugettext as _
from django.views.decorators.csrf import csrf_protect
from django.template.defaultfilters import slugify


from pod.video.models import Video, Channel, Theme
from pod.video.views import get_note_form, get_video_access
from pod.video.forms import VideoPasswordForm
from .models import Interactive, InteractiveGroup
from .forms import InteractiveGroupForm
from h5pp.models import h5p_contents, h5p_libraries
from h5pp.h5p.h5pmodule import getUserScore, h5pGetContentId


@csrf_protect
@staff_member_required(redirect_field_name='referrer')
def group_interactive(request, slug):
    video = get_object_or_404(Video, slug=slug)
    interactiveGroup, created = InteractiveGroup.objects.get_or_create(
        video=video)
    if request.user != video.owner and not request.user.is_superuser:
        messages.add_message(
            request, messages.ERROR, _(u'You cannot add interactivity to this video.'))
        raise PermissionDenied

    form = InteractiveGroupForm(instance=interactiveGroup)
    if request.POST:
        form = InteractiveGroupForm(request.POST, instance=interactiveGroup)
        if form.is_valid():
            interactiveGroup = form.save()

    return render(
        request,
        'interactive/group_interactive.html',
        {'video': video,
         'form': form})


def check_interactive_group(request, video):
    print(hasattr(video, 'interactivegroup'))
    if not hasattr(video, 'interactivegroup'):
        return False
    if not request.user.groups.filter(
        name__in=[
            name[0]
            for name in video.interactivegroup.groups.values_list('name')
        ]
    ).exists():
        return False

    return True


@csrf_protect
@staff_member_required(redirect_field_name='referrer')
def edit_interactive(request, slug):
    video = get_object_or_404(Video, slug=slug)
    if request.user != video.owner and not request.user.is_superuser:
        if not check_interactive_group(request, video):
            messages.add_message(
                request, messages.ERROR, _(u'You cannot add interactivity to this video.'))
            raise PermissionDenied

    interactiveVideo, created = Interactive.objects.get_or_create(
        video=video)

    version = h5p_libraries.objects.get(machine_name='H5P.InteractiveVideo')

    h5p = h5p_contents.objects.get(title=video.title) if (
        video.interactive.is_interactive()) else None

    interactive = {'h5p': h5p, 'version': version}

    return render(
        request,
        'interactive/edit_interactive.html',
        {'video': video,
         'interactive': interactive})


@csrf_protect
def video_interactive(request, slug, slug_c=None,
                      slug_t=None, slug_private=None):
    try:
        id = int(slug[:slug.find("-")])
    except ValueError:
        raise SuspiciousOperation('Invalid video id')
    video = get_object_or_404(Video, id=id)
    notesForm = get_note_form(request, video)
    channel = get_object_or_404(Channel, slug=slug_c) if slug_c else None
    theme = get_object_or_404(Theme, slug=slug_t) if slug_t else None
    playlist = None

    interactiveVideo, created = Interactive.objects.get_or_create(
        video=video)

    h5p = h5p_contents.objects.get(title=video.title) if (
        video.interactive.is_interactive()) else None

    score = getUserScore(h5p.content_id) if (
        request.user == video.owner or request.user.is_superuser
    ) else getUserScore(h5p.content_id, request.user).get(0)

    interactive = {'h5p': h5p, 'score': score}

    template_video = 'interactive/video_interactive-iframe.html' if (
        request.GET.get('is_iframe')) else 'interactive/video_interactive.html'

    is_password_protected = (video.password is not None)

    show_page = get_video_access(request, video, slug_private)

    if show_page:
        return render(
            request, template_video, {
                'channel': channel,
                'video': video,
                'theme': theme,
                'notesForm': notesForm,
                'playlist': playlist,
                'interactive':interactive
            }
        )
    else:
        if is_password_protected:
            form = VideoPasswordForm(
                request.POST) if request.POST else VideoPasswordForm()
            return render(
                request, 'interactive/video_interactive.html', {
                    'channel': channel,
                    'video': video,
                    'theme': theme,
                    'form': form,
                    'notesForm': notesForm
                }
            )
        elif request.user.is_authenticated():
            messages.add_message(
                request, messages.ERROR,
                _(u'You cannot watch this video.'))
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
