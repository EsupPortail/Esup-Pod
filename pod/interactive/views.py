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


from pod.video.models import Video
from .models import InteractiveVideo, InteractiveGroup
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
            request, messages.ERROR, _(u'You cannot enrich this video.'))
        raise PermissionDenied

    form = InteractiveGroupForm(instance=enrichmentGroup)
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
    """
    if not hasattr(video, 'enrichmentgroup'):
        return False
    if not request.user.groups.filter(
        name__in=[
            name[0]
            for name in video.enrichmentgroup.groups.values_list('name')
        ]
    ).exists():
        return False
    """
    return True


@csrf_protect
@staff_member_required(redirect_field_name='referrer')
def edit_interactive(request, slug):
    video = get_object_or_404(Video, slug=slug)
    if request.user != video.owner and not request.user.is_superuser:
        if not check_interactive_group(request, video):
            messages.add_message(
                request, messages.ERROR, _(u'You cannot enrich this video.'))
            raise PermissionDenied

    interactiveVideo, created = InteractiveVideo.objects.get_or_create(
        video=video)

    version = h5p_libraries.objects.get(machine_name='H5P.InteractiveVideo')

    h5p = h5p_contents.objects.get(title=video.title) if (
        video.interactivevideo.is_interactive()) else None

    interactive = {'h5p': h5p, 'version': version}

    return render(
        request,
        'interactive/edit_interactive.html',
        {'video': video,
         'interactive': interactive})
