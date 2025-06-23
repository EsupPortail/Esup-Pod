import os
import shutil

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.utils.text import slugify
from django.utils.translation import gettext as _
from pod.completion.models import Contributor, Document
from pod.main.utils import display_message_with_icon
from pod.speaker.models import JobVideo
from pod.video.models import Video


def generate_unique_slug(base_slug: str) -> str:
    """
    Generates a unique slug based on the given base slug.
    Args:
        base_slug (str): The base slug to be made unique.
    Returns:
        str: A unique slug based on the given base slug
    """
    slug = base_slug
    counter = 1
    while Video.objects.filter(slug=slug).exists():
        slug = f"{base_slug}-{counter}"
        counter += 1
    return slug


def duplicate_source_file(new_id: int, source_path: str, source_name: str) -> str:
    """
    Copies the source video file and returns the new file name.
    Args:
        new_id (int): The id of the duplicated video.
        source_path (str): The source path of the initial video.
        source_name (str): The source name of the initial video.
    Returns:
        str: The source name for the duplicated video.
    """
    try:
        # Source path (Ex: /usr/local/media/videos/xxx/video.mp4)
        name, extension = os.path.splitext(os.path.basename(source_path))
        # Generate a new file name to avoid conflicts
        new_name = f"{name}_{new_id}{extension}"
        # New source path (Ex: /usr/local/media/videos/xxx/video_lqweSNT.mp4)
        new_source_path = os.path.join(os.path.dirname(source_path), new_name)
        # New file name (Ex: videos/xxxx/video_lqweSNT.mp4)
        new_source_name = os.path.join(os.path.dirname(source_name), new_name)
        # Copy the source file
        shutil.copyfile(source_path, new_source_path)

        # Return the new file name
        return new_source_name
    except Exception as exc:
        raise ValueError(str(exc))


@login_required
def video_duplicate(request, slug):
    """
    Duplicates a video and its related objects (contributors, speakers, documents) based on the given slug.
    Args:
        request (HttpRequest): The HTTP request object containing user information.
        slug (str): The slug of the original video to be duplicated.
    Returns:
        HttpResponseRedirect: A redirect to the newly duplicated video's detail page.
    The duplicated video will have the following properties copied from the original video:
        - title (prefixed with "Copy of ")
        - slug (suffixed with "-copy")
        - source file (a copy of the source video file)
        - type
        - owner (set to the current user)
        - description, description_fr, description_en
        - date_evt
        - cursus
        - main_lang
        - licence
        - thumbnail
        - is_draft (set to True)
        - is_restricted
        - password
        - allow_downloading
        - is_360
        - transcript
        - date_delete
        - disable_comment
        - tags
    Additionally, the following many-to-many relationships are copied:
        - discipline
        - restrict_access_to_groups
        - channel
        - theme
        - additional_owners
    The following related objects are also duplicated:
        - Contributors
        - JobVideo (speakers)
        - Documents
    """

    try:
        original_video = get_object_or_404(Video, slug=slug)
        new_slug = generate_unique_slug(
            slugify(_("%(slug)s-copy") % {"slug": original_video.slug})
        )

        duplicated_video = Video.objects.create(
            title=_("Copy of %(title)s") % {"title": original_video.title},
            video=original_video.video,
            slug=new_slug,
            type=original_video.type,
            owner=request.user,
            description=original_video.description,
            description_fr=original_video.description_fr,
            description_en=original_video.description_en,
            date_evt=original_video.date_evt,
            cursus=original_video.cursus,
            main_lang=original_video.main_lang,
            licence=original_video.licence,
            thumbnail=original_video.thumbnail,
            is_draft=True,
            is_restricted=original_video.is_restricted,
            password=original_video.password,
            allow_downloading=original_video.allow_downloading,
            is_360=original_video.is_360,
            transcript=original_video.transcript,
            date_delete=original_video.date_delete,
            disable_comment=original_video.disable_comment,
            tags=original_video.tags.get_tag_list(),
            scheduled_publish_date=original_video.scheduled_publish_date,
        )
        # Duplicate the source file and assign it to the duplicated video
        duplicated_video.video.name = duplicate_source_file(
            duplicated_video.id, duplicated_video.video.path, duplicated_video.video.name
        )

        # Many-to-Many Relations
        duplicated_video.discipline.set(original_video.discipline.all())
        duplicated_video.restrict_access_to_groups.set(
            original_video.restrict_access_to_groups.all()
        )
        duplicated_video.channel.set(original_video.channel.all())
        duplicated_video.theme.set(original_video.theme.all())
        duplicated_video.additional_owners.set(original_video.additional_owners.all())

        # Copying contributors
        for contributor in Contributor.objects.filter(video=original_video):
            Contributor.objects.create(
                video=duplicated_video,
                name=contributor.name,
                email_address=contributor.email_address,
                role=contributor.role,
                weblink=contributor.weblink,
            )

        # Copying speakers
        for job_video in JobVideo.objects.filter(video=original_video):
            JobVideo.objects.create(
                job=job_video.job,
                video=duplicated_video,
            )

        # Copying documents
        for document in Document.objects.filter(video=original_video):
            Document.objects.create(
                video=duplicated_video,
                document=document.document,
                private=document.private,
            )

        # Save and encode
        duplicated_video.launch_encode = True
        duplicated_video.save()
    except ValueError as exc:
        display_message_with_icon(request, messages.ERROR, str(exc))

    return redirect(reverse("video:video_edit", args=[duplicated_video.slug]))
