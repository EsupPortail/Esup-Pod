"""
Esup-Pod - Video duplication service.
"""

from django.db import transaction
from django.utils.text import slugify
from django.utils.translation import gettext_lazy as _

from src.apps.video.models import Video
from src.apps.video.services.sites import assign_default_site

from .files import duplicate_source_file
from .slug import generate_unique_slug


@transaction.atomic
def duplicate_video(original: Video, user, request=None):
    """
    Duplicates a Video instance for the given user.

    Creates a new Video in DRAFT status with all scalar fields copied,
    the source file physically duplicated on disk, and all M2M relations
    (disciplines, restricted_groups, co_owners) mirrored.
    """

    base_slug = f"{original.slug}-copy"
    new_slug = generate_unique_slug(slugify(base_slug))

    duplicated = Video.objects.create(
        title=_("Copy of %(title)s") % {"title": original.title},
        slug=new_slug,
        type=original.type,
        owner=user,
        description=original.description,
        is_auth_required=original.is_auth_required,
        password=original.password,
        allow_downloading=original.allow_downloading,
        is_360=original.is_360,
        transcript_language=original.transcript_language,
        license=original.license,
        cursus=original.cursus,
        language=original.language,
        thumbnail=original.thumbnail,
        status=Video.Status.DRAFT,
        channel=original.channel,
        date_of_event=original.date_of_event,
        disable_comment=original.disable_comment,
        tags=original.get_tag_list(),
    )

    if original.sites.exists():
        duplicated.sites.set(original.sites.all())
    elif request:
        assign_default_site(duplicated, request)
    else:
        raise ValueError(_("Video must have at least one site"))

    if original.video_file:
        duplicated.video_file.name = duplicate_source_file(
            duplicated.id,
            original.video_file.path,
            original.video_file.name,
        )
        duplicated.save(update_fields=["video_file"])

    duplicated.disciplines.set(original.disciplines.all())
    duplicated.restricted_groups.set(original.restricted_groups.all())
    duplicated.co_owners.set(original.co_owners.all())

    # themes are added via ThemeVideo explicitly or M2M set
    if hasattr(original, "themes") and original.themes.exists():
        duplicated.themes.set(original.themes.all())

    # Copy Subtitles
    for subtitle in original.subtitles.all():
        from src.apps.video.models import Subtitle

        Subtitle.objects.create(
            video=duplicated,
            language=subtitle.language,
            file=subtitle.file,
            is_default=subtitle.is_default,
        )

    # Copy Hyperlinks
    for hyperlink in original.hyperlinks.all():
        from src.apps.video.models import VideoHyperlink

        VideoHyperlink.objects.create(
            video=duplicated,
            url=hyperlink.url,
            text=hyperlink.text,
            icon=hyperlink.icon,
            position=hyperlink.position,
            time_start=hyperlink.time_start,
            time_end=hyperlink.time_end,
        )

    if duplicated.video_file:
        from src.apps.encoding.tasks import trigger_runner_encoding_task
        from src.apps.video.conf import video_settings

        site_url = video_settings.site_url.rstrip("/")
        source_url = f"{site_url}{duplicated.video_file.url}"
        trigger_runner_encoding_task.delay(duplicated.pk, source_url)

    return duplicated
