from django.shortcuts import render
from pod.main.views import in_maintenance
from django.shortcuts import redirect
from django.urls import reverse
from django.shortcuts import get_object_or_404
from django.contrib.sites.shortcuts import get_current_site
from django.contrib.auth.decorators import login_required
from django.utils.translation import ugettext as _
from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.http import QueryDict
from django.views.decorators.csrf import csrf_protect

from pod.video_encode_transcript.encode import start_encode
from pod.video.models import Video

from .models import CutVideo
from .forms import CutVideoForm
from .utils import clean_database

from pod.video.models import RESTRICT_EDIT_VIDEO_ACCESS_TO_STAFF_ONLY


@csrf_protect
@login_required(redirect_field_name="referrer")
def cut_video(request, slug):  # noqa: C901
    """View for video cutting"""
    if in_maintenance():
        return redirect(reverse("maintenance"))
    video = get_object_or_404(Video, slug=slug, sites=get_current_site(request))
    cutting = ""

    # Get the full duration
    duration = video.duration_in_time
    if CutVideo.objects.filter(video=video.id).exists():
        cutting = CutVideo.objects.get(video=video.id)
        duration = cutting.duration

    if RESTRICT_EDIT_VIDEO_ACCESS_TO_STAFF_ONLY and request.user.is_staff is False:
        return render(request, "video_cut.html", {"access_not_allowed": True})

    if (
        video
        and request.user != video.owner
        and (
            not (request.user.is_superuser or request.user.has_perm("video.change_video"))
        )
        and (request.user not in video.additional_owners.all())
    ):
        messages.add_message(request, messages.ERROR, _("You cannot cut this video."))
        raise PermissionDenied

    form_cut = CutVideoForm()

    if request.method == "POST":
        cut = QueryDict(mutable=True)
        cut.update(request.POST)
        cut.update({"video": video.id})
        cut.update({"duration": duration})
        form_cut = CutVideoForm(cut)
        if form_cut.is_valid():
            # Delete previous object(s)
            if CutVideo.objects.filter(video=video.id).exists():
                previous = CutVideo.objects.filter(video=video.id)
                previous.delete()

            # Save the new one
            form_cut.save()

            clean_database(video.id)

            start_encode(video.id)

            messages.add_message(request, messages.INFO, _("The cut was made."))
            return redirect(reverse("video:dashboard"))

        else:
            messages.add_message(
                request,
                messages.ERROR,
                _("Please select values between 00:00:00 and ") + str(duration) + ".",
            )

    return render(
        request,
        "video_cut.html",
        {"cutting": cutting, "video": video, "form_cut": form_cut},
    )
