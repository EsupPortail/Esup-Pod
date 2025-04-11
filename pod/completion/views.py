"""Esup-Pod completion views."""

from django.conf import settings
from django.contrib import messages
from django.http import HttpResponse, JsonResponse
from django.template.loader import render_to_string
from django.shortcuts import render
from django.shortcuts import get_object_or_404
from django.utils.translation import gettext as _
from django.views.decorators.csrf import csrf_protect
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.core.exceptions import PermissionDenied
from django.core.handlers.wsgi import WSGIRequest
from pod.video.models import Video
from pod.main.utils import is_ajax
from .models import Contributor
from .forms import ContributorForm
from .models import Document
from .forms import DocumentForm
from .models import Track
from .forms import TrackForm
from .models import Overlay
from .forms import OverlayForm
from .models import CustomFileModel
from pod.speaker.models import JobVideo
from pod.speaker.forms import JobVideoForm
from pod.podfile.views import get_current_session_folder, file_edit_save
from pod.main.lang_settings import ALL_LANG_CHOICES, PREF_LANG_CHOICES
from pod.main.settings import LANGUAGE_CODE
import re
import json
from django.contrib.sites.shortcuts import get_current_site
from .utils import get_video_completion_context
from pod.speaker.utils import get_video_speakers
from pod.hyperlinks.models import VideoHyperlink
from pod.hyperlinks.forms import VideoHyperlinkForm, HyperlinkForm
from pod.completion.permissions.video import has_video_rights
from pod.video.queryset.utils import prefetch_video_completion_hyperlink

LINK_SUPERPOSITION = getattr(settings, "LINK_SUPERPOSITION", False)
ACTIVE_MODEL_ENRICH = getattr(settings, "ACTIVE_MODEL_ENRICH", False)
__AVAILABLE_ACTIONS__ = ["new", "save", "modify", "delete"]
__CAPTION_MAKER_ACTION__ = ["save"]
LANG_CHOICES = getattr(
    settings,
    "LANG_CHOICES",
    (
        (_("-- Frequently used languages --"), PREF_LANG_CHOICES),
        (_("-- All languages --"), ALL_LANG_CHOICES),
    ),
)
__LANG_CHOICES_DICT__ = {
    key: value for key, value in LANG_CHOICES[0][1] + LANG_CHOICES[1][1]
}


def get_completion_home_page_title(video: Video) -> str:
    """Get page title."""
    return _("Additions for the video “%s”") % video.title


@csrf_protect
@staff_member_required(redirect_field_name="referrer")
def video_caption_maker(request, slug):
    """Caption maker app."""
    video = get_object_or_404(Video, slug=slug, sites=get_current_site(request))

    request.session["current_session_folder"] = video.slug
    action = None
    if (
        request.user != video.owner
        and not (
            request.user.is_superuser or request.user.has_perm("completion.add_track")
        )
        and (request.user not in video.additional_owners.all())
    ):
        messages.add_message(
            request, messages.ERROR, _("You cannot complement this video.")
        )
        raise PermissionDenied
    video_folder = video.get_or_create_video_folder()
    if request.method == "POST" and request.POST.get("action"):
        action = request.POST.get("action")
    if action in __CAPTION_MAKER_ACTION__:
        return eval("video_caption_maker_{0}".format(action))(request, video)
    else:
        track_language = LANGUAGE_CODE
        track_kind = "captions"
        caption_file_id = request.GET.get("src")
        if caption_file_id:
            caption_file = CustomFileModel.objects.filter(id=caption_file_id).first()
            if caption_file:
                track = Track.objects.filter(video=video, src=caption_file).first()
                if track:
                    track_language = track.lang
                    track_kind = track.kind

        form_caption = TrackForm(initial={"video": video})
        return render(
            request,
            "video_caption_maker.html",
            {
                "current_folder": video_folder,
                "form_make_caption": form_caption,
                "video": video,
                "languages": LANG_CHOICES,
                "track_language": track_language,
                "track_kind": track_kind,
                "active_model_enrich": ACTIVE_MODEL_ENRICH,
                "page_title": _("Video caption maker"),
            },
        )


@csrf_protect
@staff_member_required(redirect_field_name="referrer")
def video_caption_maker_save(request, video):
    """Caption maker save view."""
    video_folder = video.get_or_create_video_folder()

    if request.method == "POST":
        error = False
        lang = request.POST.get("lang")
        kind = request.POST.get("kind")

        enrich_ready = True if request.POST.get("enrich_ready") == "true" else False
        cur_folder = get_current_session_folder(request)
        response = file_edit_save(request, cur_folder)
        response_data = json.loads(response.content)
        if ("list_element" in response_data) and (lang in __LANG_CHOICES_DICT__):
            capt_file = get_object_or_404(CustomFileModel, id=response_data["file_id"])
            # immediately assign the newly created captions file to the video
            desired = Track.objects.filter(video=video, src=capt_file)
            if desired.exists():
                desired.update(
                    lang=lang, kind=kind, src=capt_file, enrich_ready=enrich_ready
                )
            else:
                # check if the same combination of lang and kind exists
                if not Track.objects.filter(video=video, kind=kind, lang=lang).exists():
                    track = Track(
                        video=video,
                        kind=kind,
                        lang=lang,
                        src=capt_file,
                        enrich_ready=enrich_ready,
                    )
                    track.save()
                    return JsonResponse({"track_id": track.src_id})
                else:
                    error = True
                    messages.add_message(
                        request,
                        messages.WARNING,
                        _("There is already a file with the same kind and language."),
                    )
            if not error:
                messages.add_message(
                    request, messages.INFO, _("The file has been saved.")
                )
        else:
            messages.add_message(
                request, messages.WARNING, _("The file has not been saved.")
            )
    form_caption = TrackForm(initial={"video": video})

    return render(
        request,
        "video_caption_maker.html",
        {
            "current_folder": video_folder,
            "form_make_caption": form_caption,
            "video": video,
            "page_title": _("Video caption maker"),
        },
    )


@csrf_protect
@login_required(redirect_field_name="referrer")
def video_completion(request: WSGIRequest, slug: str):
    """Video Completion view."""
    video = get_object_or_404(Video, slug=slug, sites=get_current_site(request))
    page_title = get_completion_home_page_title(video)
    if (
        request.user != video.owner
        and not (
            request.user.is_superuser
            or (
                request.user.has_perm("completion.add_contributor")
                and request.user.has_perm("completion.add_speaker")
                and request.user.has_perm("completion.add_track")
                and request.user.has_perm("completion.add_document")
                and request.user.has_perm("completion.add_overlay")
                and request.user.has_perm("completion.add_hyperlink")
            )
        )
        and (request.user not in video.additional_owners.all())
    ):
        messages.add_message(
            request, messages.ERROR, _("You cannot complement this video.")
        )
        raise PermissionDenied
    elif request.user.is_staff:
        list_contributor = video.contributor_set.all()
        list_speaker = get_video_speakers(video)
        list_track = video.track_set.all().order_by("lang")
        list_document = video.document_set.all()
        list_overlay = video.overlay_set.all()
        list_hyperlink = VideoHyperlink.objects.filter(video=video)
    else:
        list_contributor = video.contributor_set.all()

    if request.user.is_staff:
        return render(
            request,
            "video_completion.html",
            {
                "page_title": page_title,
                "video": video,
                "list_contributor": list_contributor,
                "list_speaker": list_speaker,
                "list_track": list_track,
                "list_document": list_document,
                "list_overlay": list_overlay,
                "list_hyperlink": list_hyperlink,
            },
        )
    else:
        return render(
            request,
            "video_completion.html",
            {
                "page_title": page_title,
                "video": video,
                "list_contributor": list_contributor,
            },
        )


@csrf_protect
@login_required(redirect_field_name="referrer")
def video_completion_contributor(request: WSGIRequest, slug: str):
    """View to manage contributors of a video."""
    video = get_object_or_404(Video, slug=slug, sites=get_current_site(request))
    page_title = get_completion_home_page_title(video)
    if request.user != video.owner and not (
        request.user.is_superuser
        or request.user.has_perm("completion.add_contributor")
        or (request.user in video.additional_owners.all())
    ):
        messages.add_message(
            request, messages.ERROR, _("You cannot complement this video.")
        )
        raise PermissionDenied
    elif request.user.is_staff:
        list_contributor = video.contributor_set.all()
        list_speaker = get_video_speakers(video)
        list_track = video.track_set.all().order_by("lang")
        list_document = video.document_set.all()
        list_overlay = video.overlay_set.all()
    else:
        list_contributor = video.contributor_set.all()
    if request.POST and request.POST.get("action"):
        if request.POST["action"] in __AVAILABLE_ACTIONS__:
            return eval(
                "video_completion_contributor_{0}(request, video)".format(
                    request.POST["action"]
                )
            )

    elif request.user.is_staff:
        return render(
            request,
            "video_completion.html",
            {
                "page_title": page_title,
                "video": video,
                "list_contributor": list_contributor,
                "list_speaker": list_speaker,
                "list_track": list_track,
                "list_document": list_document,
                "list_overlay": list_overlay,
            },
        )
    else:
        return render(
            request,
            "video_completion.html",
            {
                "page_title": page_title,
                "video": video,
                "list_contributor": list_contributor,
            },
        )


def video_completion_contributor_new(request: WSGIRequest, video: Video):
    """View to add new contributor to a video."""
    form_contributor = ContributorForm(initial={"video": video})
    context = get_video_completion_context(video, form_contributor=form_contributor)
    context["page_title"] = _("Add a new contributor to the video “%s”") % video.title
    if is_ajax(request):
        return render(
            request,
            "contributor/form_contributor.html",
            {
                "page_title": context["page_title"],
                "form_contributor": form_contributor,
                "video": video,
            },
        )
    else:
        return render(
            request,
            "video_completion.html",
            context,
        )


def video_completion_contributor_save(request: WSGIRequest, video: Video):
    """View to save contributors of a video."""
    form_contributor = None
    if request.POST.get("contributor_id") and request.POST["contributor_id"] != "None":
        contributor = get_object_or_404(Contributor, id=request.POST["contributor_id"])
        form_contributor = ContributorForm(request.POST, instance=contributor)
    else:
        form_contributor = ContributorForm(request.POST)
    if form_contributor.is_valid():
        form_contributor.save()
        list_contributor = video.contributor_set.all()
        if is_ajax(request):
            some_data_to_dump = {
                "list_data": render_to_string(
                    "contributor/list_contributor.html",
                    {
                        "page_title": _("Add a new contributor to the video “%s”")
                        % video.title,
                        "list_contributor": list_contributor,
                        "video": video,
                    },
                    request=request,
                ),
            }
            data = json.dumps(some_data_to_dump)
            return HttpResponse(data, content_type="application/json")
        else:
            context = get_video_completion_context(
                video, list_contributor=list_contributor
            )
            context["page_title"] = get_completion_home_page_title(video)
            messages.add_message(
                request, messages.SUCCESS, _("The contributor has been saved.")
            )
            return render(
                request,
                "video_completion.html",
                context,
            )
    else:
        if is_ajax(request):
            some_data_to_dump = {
                "errors": "{0}".format(_("Please correct errors")),
                "form": render_to_string(
                    "contributor/form_contributor.html",
                    {
                        "page_title": _("Add a new contributor to the video “%s”")
                        % video.title,
                        "video": video,
                        "form_contributor": form_contributor,
                    },
                    request=request,
                ),
            }
            data = json.dumps(some_data_to_dump)
            return HttpResponse(data, content_type="application/json")
        context = get_video_completion_context(video, form_contributor=form_contributor)
        context["page_title"] = get_completion_home_page_title(video)
        return render(
            request,
            "video_completion.html",
            context,
        )


def video_completion_contributor_modify(request: WSGIRequest, video: Video):
    """View to modify a video contributor."""
    contributor = get_object_or_404(Contributor, id=request.POST["id"])
    form_contributor = ContributorForm(instance=contributor)
    page_title = _("Edit the contributor “%s”") % contributor.name
    if is_ajax(request):
        return render(
            request,
            "contributor/form_contributor.html",
            {
                "page_title": page_title,
                "form_contributor": form_contributor,
                "video": video,
            },
        )
    context = get_video_completion_context(video, form_contributor=form_contributor)
    context["page_title"] = page_title
    return render(
        request,
        "video_completion.html",
        context,
    )


def video_completion_contributor_delete(request: WSGIRequest, video: Video):
    """View to delete a video contributor."""
    contributor = get_object_or_404(Contributor, id=request.POST["id"])
    contributor.delete()
    page_title = get_completion_home_page_title(video)
    list_contributor = video.contributor_set.all()
    if is_ajax(request):
        some_data_to_dump = {
            "list_data": render_to_string(
                "contributor/list_contributor.html",
                {
                    "page_title": page_title,
                    "list_contributor": list_contributor,
                    "video": video,
                },
                request=request,
            )
        }
        data = json.dumps(some_data_to_dump)
        return HttpResponse(data, content_type="application/json")
    context = get_video_completion_context(video)
    context["page_title"] = page_title
    return render(
        request,
        "video_completion.html",
        context,
    )


@csrf_protect
@login_required(redirect_field_name="referrer")
def video_completion_speaker(request: WSGIRequest, slug: str):
    """View to manage speakers of a video."""
    video = get_object_or_404(Video, slug=slug, sites=get_current_site(request))
    page_title = get_completion_home_page_title(video)
    if request.user != video.owner and not (
        request.user.is_superuser
        or request.user.has_perm("completion.add_speaker")
        or (request.user in video.additional_owners.all())
    ):
        messages.add_message(
            request, messages.ERROR, _("You cannot complement this video.")
        )
        raise PermissionDenied
    elif request.user.is_staff:
        list_contributor = video.contributor_set.all()
        list_speaker = get_video_speakers(video)
        list_track = video.track_set.all().order_by("lang")
        list_document = video.document_set.all()
        list_overlay = video.overlay_set.all()
    else:
        list_contributor = video.contributor_set.all()
    if request.POST and request.POST.get("action"):
        if request.POST["action"] in __AVAILABLE_ACTIONS__:
            return eval(
                "video_completion_speaker_{0}(request, video)".format(
                    request.POST["action"]
                )
            )

    elif request.user.is_staff:
        return render(
            request,
            "video_completion.html",
            {
                "page_title": page_title,
                "video": video,
                "list_contributor": list_contributor,
                "list_speaker": list_speaker,
                "list_track": list_track,
                "list_document": list_document,
                "list_overlay": list_overlay,
            },
        )
    else:
        return render(
            request,
            "video_completion.html",
            {
                "page_title": page_title,
                "video": video,
                "list_contributor": list_contributor,
            },
        )


def video_completion_speaker_new(request: WSGIRequest, video: Video):
    """View to add new speaker to a video."""
    form_speaker = JobVideoForm(initial={"video": video})
    context = get_video_completion_context(video, form_speaker=form_speaker)
    context["page_title"] = _("Add a new contributor to the video “%s”") % video.title
    if is_ajax(request):
        return render(
            request,
            "speaker/form_speaker.html",
            {
                "page_title": context["page_title"],
                "form_speaker": form_speaker,
                "video": video,
            },
        )
    else:
        return render(
            request,
            "video_completion.html",
            context,
        )


def video_completion_speaker_save(request: WSGIRequest, video: Video):
    """View to save speakers of a video."""
    form_speaker = None
    form_speaker = JobVideoForm(request.POST)
    if form_speaker.is_valid():
        form_speaker.save()
        list_speaker = get_video_speakers(video)
        if is_ajax(request):
            some_data_to_dump = {
                "list_data": render_to_string(
                    "speaker/list_speaker.html",
                    {
                        "page_title": _("Add a new speaker to the video “%s”")
                        % video.title,
                        "list_speaker": list_speaker,
                        "video": video,
                    },
                    request=request,
                ),
            }
            data = json.dumps(some_data_to_dump)
            return HttpResponse(data, content_type="application/json")
        else:
            context = get_video_completion_context(video, list_speaker=list_speaker)
            context["page_title"] = get_completion_home_page_title(video)
            messages.add_message(
                request, messages.SUCCESS, _("The speaker has been saved.")
            )
            return render(
                request,
                "video_completion.html",
                context,
            )
    else:
        if is_ajax(request):
            some_data_to_dump = {
                "errors": "{0}".format(_("Please correct errors")),
                "form": render_to_string(
                    "speaker/form_speaker.html",
                    {
                        "page_title": _("Add a new speaker to the video “%s”")
                        % video.title,
                        "video": video,
                        "form_speaker": form_speaker,
                    },
                    request=request,
                ),
            }
            data = json.dumps(some_data_to_dump)
            return HttpResponse(data, content_type="application/json")
        context = get_video_completion_context(video, form_speaker=form_speaker)
        context["page_title"] = get_completion_home_page_title(video)
        return render(
            request,
            "video_completion.html",
            context,
        )


def video_completion_speaker_delete(request: WSGIRequest, video: Video):
    """View to delete a video speaker."""
    speaker = get_object_or_404(JobVideo, id=request.POST["id"])
    speaker.delete()
    page_title = get_completion_home_page_title(video)
    list_speaker = get_video_speakers(video)
    if is_ajax(request):
        some_data_to_dump = {
            "list_data": render_to_string(
                "speaker/list_speaker.html",
                {
                    "page_title": page_title,
                    "list_speaker": list_speaker,
                    "video": video,
                },
                request=request,
            )
        }
        data = json.dumps(some_data_to_dump)
        return HttpResponse(data, content_type="application/json")
    context = get_video_completion_context(video)
    context["page_title"] = page_title
    return render(
        request,
        "video_completion.html",
        context,
    )


@csrf_protect
@has_video_rights(
    ["completion.add_hyperlink"],
    "You cannot complement this video.",
    prefetch_video_completion_hyperlink
)
@login_required(redirect_field_name="referrer")
def video_completion_hyperlink(request: WSGIRequest, slug: str, video: Video):
    """View to manage hyperlinks of a video."""
    action_mapping = {
        "new": video_completion_hyperlink_new,
        "save": video_completion_hyperlink_save,
        "modify": video_completion_hyperlink_modify,
        "delete": video_completion_hyperlink_delete,
    }

    if request.method == "POST":
        action = request.POST.get("action")
        if action in action_mapping:
            return action_mapping[action](request, video)

    page_title = get_completion_home_page_title(video)
    context = {
        "page_title": page_title,
        "video": video,
    }

    return render(request, "video_completion.html", context)


def video_completion_hyperlink_new(request: WSGIRequest, video: Video):
    """View to add new hyperlink to a video."""
    form_hyperlink = VideoHyperlinkForm(initial={"video": video})
    context = get_video_completion_context(video, form_hyperlink=form_hyperlink)
    context["page_title"] = _("Add a new hyperlink to the video “%s”") % video.title
    context["form_hyperlink_is_active"] = True
    if is_ajax(request):
        return render(
            request,
            "hyperlinks/form_hyperlink.html",
            {
                "page_title": context["page_title"],
                "form_hyperlink": form_hyperlink,
                "video": video,
            },
        )
    else:
        return render(
            request,
            "video_completion.html",
            context,
        )


def video_completion_hyperlink_save(request: WSGIRequest, video: Video):
    """View to save hyperlinks of a video."""
    form_hyperlink = None
    form_hyperlink = VideoHyperlinkForm(request.POST)
    if form_hyperlink.is_valid():
        form_hyperlink.save()
        list_hyperlink = VideoHyperlink.objects.filter(video=video)
        if is_ajax(request):
            some_data_to_dump = {
                "list_data": render_to_string(
                    "hyperlinks/list_hyperlink.html",
                    {
                        "page_title": _("Add a new hyperlink to the video “%s”")
                        % video.title,
                        "list_hyperlink": list_hyperlink,
                        "video": video,
                    },
                    request=request,
                ),
            }
            data = json.dumps(some_data_to_dump)
            return HttpResponse(data, content_type="application/json")
        else:
            context = get_video_completion_context(video, list_hyperlink=list_hyperlink)
            context["page_title"] = get_completion_home_page_title(video)
            messages.add_message(
                request, messages.SUCCESS, _("The hyperlink has been saved.")
            )
            return render(
                request,
                "video_completion.html",
                context,
            )
    else:
        if is_ajax(request):
            some_data_to_dump = {
                "errors": "{0}".format(_("Please correct errors")),
                "form": render_to_string(
                    "hyperlinks/form_hyperlink.html",
                    {
                        "page_title": _("Add a new hyperlink to the video “%s”")
                        % video.title,
                        "video": video,
                        "form_hyperlink": form_hyperlink,
                    },
                    request=request,
                ),
            }
            data = json.dumps(some_data_to_dump)
            return HttpResponse(data, content_type="application/json")
        context = get_video_completion_context(video, form_hyperlink=form_hyperlink)
        context["page_title"] = get_completion_home_page_title(video)
        return render(
            request,
            "video_completion.html",
            context,
        )


@csrf_protect
@login_required(redirect_field_name="referrer")
def video_completion_hyperlink_modify(request: WSGIRequest, video: Video):
    """View to modify a video hyperlink."""
    hyperlink = get_object_or_404(VideoHyperlink, id=request.POST["id"])
    form_hyperlink = HyperlinkForm(instance=hyperlink)
    page_title = _("Edit the hyperlink “%s”") % hyperlink.url
    if is_ajax(request):
        return render(
            request,
            "hyperlinks/form_hyperlink.html",
            {
                "page_title": page_title,
                "form_hyperlink": form_hyperlink,
                "video": video,
            },
        )
    context = get_video_completion_context(video, form_hyperlink=form_hyperlink)
    context["page_title"] = page_title
    return render(
        request,
        "video_completion.html",
        context,
    )


@csrf_protect
@login_required(redirect_field_name="referrer")
def video_completion_hyperlink_delete(request: WSGIRequest, video: Video):
    """View to delete a video hyperlink."""
    hyperlink = get_object_or_404(VideoHyperlink, id=request.POST["id"])
    hyperlink.delete()
    page_title = get_completion_home_page_title(video)
    list_hyperlink = VideoHyperlink.objects.filter(video=video)
    if is_ajax(request):
        some_data_to_dump = {
            "list_data": render_to_string(
                "hyperlinks/list_hyperlink.html",
                {
                    "page_title": page_title,
                    "list_hyperlink": list_hyperlink,
                    "video": video,
                },
                request=request,
            )
        }
        data = json.dumps(some_data_to_dump)
        return HttpResponse(data, content_type="application/json")
    context = get_video_completion_context(video)
    context["page_title"] = page_title
    return render(
        request,
        "video_completion.html",
        context,
    )


@csrf_protect
@staff_member_required(redirect_field_name="referrer")
def video_completion_document(request, slug):
    """View to manage documents associated to a video."""
    video = get_object_or_404(Video, slug=slug, sites=get_current_site(request))
    if request.user != video.owner and not (
        request.user.is_superuser
        or request.user.has_perm("completion.add_document")
        or (request.user in video.additional_owners.all())
    ):
        messages.add_message(
            request, messages.ERROR, _("You cannot complement this video.")
        )
        raise PermissionDenied

    if request.POST and request.POST.get("action"):
        if request.POST["action"] in __AVAILABLE_ACTIONS__:
            return eval(
                "video_completion_document_{0}(request, video)".format(
                    request.POST["action"]
                )
            )
    else:
        context = get_video_completion_context(video)
        return render(
            request,
            "video_completion.html",
            context,
        )


def video_completion_document_new(request, video):
    """View to add new document to a video."""
    form_document = DocumentForm(initial={"video": video})
    context = get_video_completion_context(video, form_document=form_document)
    if is_ajax(request):
        return render(
            request,
            "document/form_document.html",
            {"form_document": form_document, "video": video},
        )
    else:
        return render(
            request,
            "video_completion.html",
            context,
        )


def video_completion_document_save(request, video):
    """View to save document associated to a video."""
    form_document = None
    form_document = DocumentForm(request, request.POST)
    if (
        request.POST.get("id-instance-document")
        and request.POST["id-instance-document"] != "None"
    ):
        document = get_object_or_404(Document, id=request.POST["id-instance-document"])
        form_document = DocumentForm(request.POST, instance=document)
    else:
        form_document = DocumentForm(request.POST)
    context = get_video_completion_context(video, form_document=form_document)
    if form_document.is_valid():
        form_document.save()
        list_document = video.document_set.all()
        context = get_video_completion_context(video, list_document=list_document)
        if is_ajax(request):
            some_data_to_dump = {
                "list_data": render_to_string(
                    "document/list_document.html",
                    {"list_document": list_document, "video": video},
                    request=request,
                )
            }
            data = json.dumps(some_data_to_dump)
            return HttpResponse(data, content_type="application/json")
        else:
            return render(
                request,
                "video_completion.html",
                context,
            )
    else:
        if is_ajax(request):
            some_data_to_dump = {
                "errors": "{0}".format(_("Please correct errors")),
                "form": render_to_string(
                    "document/form_document.html",
                    {"video": video, "form_document": form_document},
                    request=request,
                ),
            }
            data = json.dumps(some_data_to_dump)
            return HttpResponse(data, content_type="application/json")
        else:
            return render(
                request,
                "video_completion.html",
                context,
            )


def video_completion_document_modify(request, video):
    """View to modify a document associated to a video."""
    document = get_object_or_404(Document, id=request.POST["id"])
    form_document = DocumentForm(instance=document)
    if is_ajax(request):
        return render(
            request,
            "document/form_document.html",
            {"form_document": form_document, "video": video},
        )
    else:
        context = get_video_completion_context(video, form_document=form_document)
        return render(
            request,
            "video_completion.html",
            context,
        )


def video_completion_document_delete(request, video):
    """View to delete a document associated to a video."""
    document = get_object_or_404(Document, id=request.POST["id"])
    document.delete()
    list_document = video.document_set.all()
    if is_ajax(request):
        some_data_to_dump = {
            "list_data": render_to_string(
                "document/list_document.html",
                {"list_document": list_document, "video": video},
                request=request,
            )
        }
        data = json.dumps(some_data_to_dump)
        return HttpResponse(data, content_type="application/json")
    else:
        context = get_video_completion_context(video, list_document=list_document)
        return render(
            request,
            "video_completion.html",
            context,
        )


@csrf_protect
@staff_member_required(redirect_field_name="referrer")
def video_completion_track(request, slug):
    """View to manage tracks associated to a video."""
    video = get_object_or_404(Video, slug=slug, sites=get_current_site(request))
    if request.user != video.owner and not (
        request.user.is_superuser
        or request.user.has_perm("completion.add_track")
        or (request.user in video.additional_owners.all())
    ):
        messages.add_message(
            request, messages.ERROR, _("You cannot complement this video.")
        )
        raise PermissionDenied

    if request.POST and request.POST.get("action"):
        if request.POST["action"] in __AVAILABLE_ACTIONS__:
            return eval(
                "video_completion_track_{0}(request, video)".format(
                    request.POST["action"]
                )
            )
    else:
        context = get_video_completion_context(video)
        return render(
            request,
            "video_completion.html",
            context,
        )


def video_completion_track_new(request, video):
    """View to add new track to a video."""
    form_track = TrackForm(initial={"video": video})
    context = get_video_completion_context(video, form_track=form_track)
    if is_ajax(request):
        return render(
            request,
            "track/form_track.html",
            {"form_track": form_track, "video": video},
        )
    else:
        return render(
            request,
            "video_completion.html",
            context,
        )


def video_completion_get_form_track(request):
    """View to get a track form associated to a video."""
    form_track = TrackForm(request.POST)
    if request.POST.get("track_id") and request.POST["track_id"] != "None":
        track = get_object_or_404(Track, id=request.POST["track_id"])
        form_track = TrackForm(request.POST, instance=track)
    else:
        form_track = TrackForm(request.POST)
    return form_track


def toggle_form_track_is_valid__video_completion_track(request, video, list_track):
    """Toggle form_track is valid."""
    if is_ajax(request):
        some_data_to_dump = {
            "list_data": render_to_string(
                "track/list_track.html",
                {"list_track": list_track, "video": video},
                request=request,
            )
        }
        data = json.dumps(some_data_to_dump)
        return HttpResponse(data, content_type="application/json")
    else:
        context = get_video_completion_context(video, list_track=list_track)
        return render(
            request,
            "video_completion.html",
            context,
        )


def video_completion_track_save(request, video):
    """View to save a track associated to a video."""
    form_track = video_completion_get_form_track(request)
    list_track = video.track_set.all().order_by("lang")

    if form_track.is_valid():
        form_track.save()
        return toggle_form_track_is_valid__video_completion_track(
            request, video, list_track
        )
    else:
        if is_ajax(request):
            some_data_to_dump = {
                "errors": "{0}".format("Please correct errors"),
                "form": render_to_string(
                    "track/form_track.html",
                    {"video": video, "form_track": form_track},
                    request=request,
                ),
            }
            data = json.dumps(some_data_to_dump)
            return HttpResponse(data, content_type="application/json")
        else:
            context = get_video_completion_context(
                video, list_track=list_track, form_track=form_track
            )
            return render(
                request,
                "video_completion.html",
                context,
            )


def video_completion_track_modify(request, video):
    """View to modify a track associated to a video."""
    track = get_object_or_404(Track, id=request.POST["id"])
    form_track = TrackForm(instance=track)
    if is_ajax(request):
        return render(
            request,
            "track/form_track.html",
            {"form_track": form_track, "video": video},
        )
    else:
        context = get_video_completion_context(video, form_track=form_track)
        return render(
            request,
            "video_completion.html",
            context,
        )


def video_completion_track_delete(request, video):
    """View to delete a track associated to a video."""
    track = get_object_or_404(Track, id=request.POST["id"])
    track.delete()
    list_track = video.track_set.all().order_by("lang")
    return toggle_form_track_is_valid__video_completion_track(request, video, list_track)


def is_already_link(url, text):
    """Test if an url is already present as HTML link in a text."""
    link_http = "<a href='{0}' target='_blank'>{1}</a>".format(url, url)
    link = "<a href='//{0}' target='_blank'>{1}</a>".format(url, url)
    return link in text or link_http in text


def transform_url_to_link(text):
    """Transform an URL to an HTML link."""
    text = " " + text
    pattern = re.compile(
        r"((https?:\/\/)?(www\.)?[-a-zA-Z0-9@:%._\+~#=]{2,256}\.[a-z]{2,6}"
        r"([-a-zA-Z0-9@:%_\+.~#?&\/\/=]*))+"
    )
    urls = re.findall(pattern, text)

    if urls:
        for url in urls:
            if not is_already_link(url[0], text):
                if "http://" in url[0] or "https://" in url[0]:
                    text = re.sub(
                        re.compile(r"\s" + re.escape(url[0])).pattern,
                        " <a href='{0}' target='_blank'>{1}</a>".format(url[0], url[0]),
                        text,
                    )
                else:
                    text = re.sub(
                        re.compile(r"\s" + re.escape(url[0])).pattern,
                        " <a href='//{0}' target='_blank'>{1}</a>".format(url[0], url[0]),
                        text,
                    )
    return text.strip()


def get_simple_url(overlay):
    pattern = re.compile(
        r"(<a\shref=['\"][^\s]+['\"]\starget=['\"][^\s]+['\"]>" r"([^\s]+)</a>)"
    )
    links = pattern.findall(overlay.content)
    for k, v in links:
        overlay.content = re.sub(k, v, overlay.content)
    return overlay


@csrf_protect
@staff_member_required(redirect_field_name="referrer")
def video_completion_overlay(request, slug):
    video = get_object_or_404(Video, slug=slug)
    if request.user != video.owner and not (
        request.user.is_superuser
        or request.user.has_perm("completion.add_overlay")
        or (request.user in video.additional_owners.all())
    ):
        messages.add_message(
            request, messages.ERROR, _("You cannot complement this video.")
        )
        raise PermissionDenied

    if request.POST and request.POST.get("action"):
        if request.POST["action"] in __AVAILABLE_ACTIONS__:
            return eval(
                "video_completion_overlay_{0}(request, video)".format(
                    request.POST["action"]
                )
            )
    else:
        context = get_video_completion_context(video)
        return render(
            request,
            "video_completion.html",
            context,
        )


def video_completion_overlay_new(request, video):
    """Form to create a new completion overlay."""
    form_overlay = OverlayForm(initial={"video": video})
    context = get_video_completion_context(video, form_overlay=form_overlay)
    if is_ajax(request):
        return render(
            request,
            "overlay/form_overlay.html",
            {"form_overlay": form_overlay, "video": video},
        )
    return render(
        request,
        "video_completion.html",
        context,
    )


def video_completion_overlay_save(request, video):
    """Save a completion overlay."""
    if LINK_SUPERPOSITION:
        request.POST._mutable = True
        request.POST["content"] = transform_url_to_link(request.POST["content"])
        request.POST._mutable = False

    form_overlay = OverlayForm(request.POST)
    if request.POST.get("overlay_id") and request.POST["overlay_id"] != "None":
        overlay = get_object_or_404(Overlay, id=request.POST["overlay_id"])
        form_overlay = OverlayForm(request.POST, instance=overlay)
    else:
        form_overlay = OverlayForm(request.POST)
    if form_overlay.is_valid():
        form_overlay.save()
        list_overlay = video.overlay_set.all()
        if is_ajax(request):
            some_data_to_dump = {
                "list_data": render_to_string(
                    "overlay/list_overlay.html",
                    {"list_overlay": list_overlay, "video": video},
                    request=request,
                )
            }
            data = json.dumps(some_data_to_dump)
            return HttpResponse(data, content_type="application/json")

        context = get_video_completion_context(video, list_overlay=list_overlay)
        return render(
            request,
            "video_completion.html",
            context,
        )
    else:
        if is_ajax(request):
            some_data_to_dump = {
                "errors": "{0}".format(_("Please correct errors")),
                "form": render_to_string(
                    "overlay/form_overlay.html",
                    {"video": video, "form_overlay": form_overlay},
                    request=request,
                ),
            }
            data = json.dumps(some_data_to_dump)
            return HttpResponse(data, content_type="application/json")
        context = get_video_completion_context(video, form_overlay=form_overlay)
        return render(
            request,
            "video_completion.html",
            context,
        )


def video_completion_overlay_modify(request, video):
    """Modify a completion overlay."""
    overlay = get_object_or_404(Overlay, id=request.POST["id"])

    if LINK_SUPERPOSITION:
        overlay = get_simple_url(overlay)

    form_overlay = OverlayForm(instance=overlay)
    if is_ajax(request):
        return render(
            request,
            "overlay/form_overlay.html",
            {"form_overlay": form_overlay, "video": video},
        )
    context = get_video_completion_context(video, form_overlay=form_overlay)
    return render(
        request,
        "video_completion.html",
        context,
    )


def video_completion_overlay_delete(request, video):
    """Delete a completion overlay."""
    overlay = get_object_or_404(Overlay, id=request.POST["id"])
    overlay.delete()
    list_overlay = video.overlay_set.all()
    if is_ajax(request):
        some_data_to_dump = {
            "list_data": render_to_string(
                "overlay/list_overlay.html",
                {"list_overlay": list_overlay, "video": video},
                request=request,
            )
        }
        data = json.dumps(some_data_to_dump)
        return HttpResponse(data, content_type="application/json")
    else:
        context = get_video_completion_context(video, list_overlay=list_overlay)
        return render(
            request,
            "video_completion.html",
            context,
        )
