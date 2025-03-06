"""Esup-Pod completion app utilities."""

from django.utils.translation import gettext as _
from pod.speaker.utils import get_video_speakers
from pod.hyperlinks.models import VideoHyperlink


def get_video_completion_context(
    video,
    list_contributor=None,
    list_speaker=None,
    list_document=None,
    list_track=None,
    list_overlay=None,
    list_hyperlink=None,
    form_contributor=None,
    form_speaker=None,
    form_document=None,
    form_track=None,
    form_overlay=None,
    form_hyperlink=None,
):
    """
    Return a dictionary containing information extracted from the video.

    and its associated objects
    (video, list of contributors, list of speakers, list of documents, track and overlay,
    as well as forms for creating or updating these objects)
    """
    if list_contributor is None:
        list_contributor = video.contributor_set.all()
    if list_speaker is None:
        list_speaker = get_video_speakers(video)
    if list_document is None:
        list_document = video.document_set.all()
    if list_track is None:
        list_track = video.track_set.all()
    if list_overlay is None:
        list_overlay = video.overlay_set.all()
    if list_hyperlink is None:
        list_hyperlink = VideoHyperlink.objects.filter(video=video)

    context = {
        "video": video,
        "list_contributor": list_contributor,
        "list_speaker": list_speaker,
        "list_document": list_document,
        "list_track": list_track,
        "list_overlay": list_overlay,
        "form_contributor": form_contributor,
        "form_speaker": form_speaker,
        "form_document": form_document,
        "form_track": form_track,
        "form_overlay": form_overlay,
        "form_hyperlink": form_hyperlink,
        "page_title": _("Additions for the video “%s”") % video.title,
    }

    return context
