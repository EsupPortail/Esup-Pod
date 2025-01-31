from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from pod.completion.models import Contributor, Document
from pod.speaker.models import JobVideo
from pod.video.models import Video
from django.contrib.auth.decorators import login_required
from django.utils.translation import gettext as _
from django.utils.text import slugify


def generate_unique_slug(base_slug):
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


@login_required
def video_duplicate(request, slug):
    """
    Duplicates a video and its related objects (contributors, speakers, documents) based on the given slug.
    Args:
        request (HttpRequest): The HTTP request object containing user information.
        slug (str): The slug of the original video to be duplicated.
    Returns:
        HttpResponseRedirect: A redirect to the newly duplicated video's detail page.
    Raises:
        Http404: If the original video with the given slug does not exist.
    The duplicated video will have the following properties copied from the original video:
        - title (prefixed with "Copy of ")
        - slug (suffixed with "-copy")
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

    original_video = get_object_or_404(Video, slug=slug)
    new_slug = generate_unique_slug(
        slugify(_("%(slug)s-copy") % {"slug": original_video.slug})
    )

    duplicated_video = Video.objects.create(
        title=_("Copy of %(title)s") % {"title": original_video.title},
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
        tags=original_video.tags,
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

    return redirect(reverse("video:video_edit", args=[duplicated_video.slug]))
