"""Esup-Pod dressing views."""

from django.shortcuts import render, redirect, get_object_or_404
from pod.main.views import in_maintenance
from django.urls import reverse
from django.contrib.sites.shortcuts import get_current_site
from django.contrib.auth.decorators import login_required
from django.utils.translation import gettext as _
from django.views.decorators.csrf import csrf_protect
from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.core.handlers.wsgi import WSGIRequest

from pod.video.models import Video
from pod.video_encode_transcript.encode import start_encode
from .forms import DressingForm, DressingDeleteForm
from .models import Dressing
from .utils import get_dressings


@csrf_protect
@login_required(redirect_field_name="referrer")
def video_dressing(request: WSGIRequest, slug: str):
    """View for video dressing."""
    if in_maintenance():
        return redirect(reverse("maintenance"))

    video = get_object_or_404(Video, slug=slug, sites=get_current_site(request))

    if not video.encoded and video.encoding_in_progress is True:
        messages.add_message(
            request, messages.ERROR, _("The video is currently being encoded.")
        )
        raise PermissionDenied

    dressings = get_dressings(request.user, request.user.owner.accessgroup_set.all())

    if not (
        request.user.is_superuser
        or (request.user == video.owner and request.user.is_staff)
    ):
        messages.add_message(request, messages.ERROR, _("You cannot dress this video."))
        raise PermissionDenied

    if request.method == "POST":
        selected_dressing_value = request.POST.get("selected_dressing_value")
        selected_dressing = (
            get_object_or_404(Dressing, pk=selected_dressing_value)
            if selected_dressing_value
            else None
        )

        existing = Dressing.objects.filter(videos=video)
        for dressing in existing:
            dressing.videos.remove(video)
            dressing.save()

        if selected_dressing:
            selected_dressing.videos.add(video)
            selected_dressing.save()

        start_encode(video.id)
        return redirect(reverse("video:video", args=(video.slug,)))

    current = Dressing.objects.filter(videos=video).first()

    return render(
        request,
        "video_dressing.html",
        {
            "page_title": _("Dress the video “%s”") % video.title,
            "video": video,
            "dressings": dressings,
            "current": current,
        },
    )


@csrf_protect
@login_required(redirect_field_name="referrer")
def dressing_edit(request: WSGIRequest, dressing_id: int):
    """Edit a dressing object."""
    dressing_edit = get_object_or_404(Dressing, id=dressing_id)

    if dressing_edit and (not (request.user.is_superuser or request.user.is_staff)):
        messages.add_message(request, messages.ERROR, _("You cannot edit this dressing."))
        raise PermissionDenied

    form_dressing = DressingForm(
        instance=dressing_edit,
        is_staff=request.user.is_staff,
        is_superuser=request.user.is_superuser,
        user=request.user,
    )

    if request.method == "POST":
        form_dressing = DressingForm(
            request.POST,
            instance=dressing_edit,
            user=request.user,
        )
        if form_dressing.is_valid():
            messages.add_message(
                request, messages.INFO, _("The changes have been saved.")
            )
            form_dressing.save()
            return redirect(reverse("dressing:my_dressings"))
    page_title = _("Edit the dressing “%s”") % dressing_edit.title
    return render(
        request,
        "dressing_edit.html",
        {
            "page_title": page_title,
            "dressing_edit": dressing_edit,
            "form": form_dressing,
        },
    )


@csrf_protect
@login_required(redirect_field_name="referrer")
def dressing_create(request: WSGIRequest):
    """Create a dressing object."""
    if not (request.user.is_superuser or request.user.is_staff):
        messages.add_message(
            request, messages.ERROR, _("You cannot create a video dressing.")
        )
        raise PermissionDenied

    if request.method == "POST":
        form_dressing = DressingForm(request.POST, user=request.user)
        if form_dressing.is_valid():
            form_dressing.save()
            return redirect("dressing:my_dressings")
    else:
        form_dressing = DressingForm(user=request.user)

    return render(
        request,
        "dressing_edit.html",
        {
            "page_title": _("Create a new dressing"),
            "dressing_create": dressing_create,
            "form": form_dressing,
        },
    )


@csrf_protect
@login_required(redirect_field_name="referrer")
def dressing_delete(request: WSGIRequest, dressing_id: int):
    """Delete the dressing identified by 'id'."""
    dressing = get_object_or_404(Dressing, id=dressing_id)
    if in_maintenance():
        return redirect(reverse("maintenance"))

    if dressing and (not (request.user.is_superuser or request.user.is_staff)):
        messages.add_message(
            request, messages.ERROR, _("You cannot delete this dressing.")
        )
        raise PermissionDenied

    form = DressingDeleteForm()

    if request.method == "POST":
        form = DressingDeleteForm(request.POST)
        if form.is_valid():
            dressing.delete()
            messages.add_message(
                request, messages.INFO, _("The dressing has been deleted.")
            )
            return redirect("dressing:my_dressings")
        else:
            messages.add_message(
                request,
                messages.ERROR,
                _("One or more errors have been found in the form."),
            )

    return render(
        request,
        "dressing_delete.html",
        {
            "page_title": _("Deleting the dressing “%s”") % dressing.title,
            "dressing": dressing,
            "form": form,
        },
    )


@csrf_protect
@login_required(redirect_field_name="referrer")
def my_dressings(request: WSGIRequest):
    """Render the logged user's dressings."""
    if in_maintenance():
        return redirect(reverse("maintenance"))

    if not (request.user.is_superuser or request.user.is_staff):
        messages.add_message(request, messages.ERROR, _("You cannot access this page."))
        raise PermissionDenied

    dressings = get_dressings(request.user, request.user.owner.accessgroup_set.all())
    return render(
        request,
        "my_dressings.html",
        {
            "page_title": _("My dressings"),
            "dressings": dressings,
        },
    )
