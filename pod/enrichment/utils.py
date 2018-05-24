import datetime
import os

from django.apps import apps
from django.conf import settings
from django.core.files import File
from django.utils import timezone
from webvtt import WebVTT, Caption
if apps.is_installed('pod.authentication'):
    from pod.authentication.models import Owner
    AUTH = True
if apps.is_installed('pod.filepicker'):
    FILEPICKER = True
    from pod.filepicker.models import CustomFileModel
    from pod.filepicker.models import UserDirectory


def enrichment_to_vtt(list_enrichment, video):
    webvtt = WebVTT()
    for enrich in list_enrichment:
        start = datetime.datetime.utcfromtimestamp(
            enrich.start).strftime('%H:%M:%S.%f')[:-3]
        end = datetime.datetime.utcfromtimestamp(
            enrich.end).strftime('%H:%M:%S.%f')[:-3]
        url = ''
        if enrich.type == 'image':
            url = enrich.image.file.url
        elif enrich.type == 'document':
            url = enrich.document.file.url
        elif enrich.type == 'richtext':
            url = enrich.richtext
        caption = Caption(
            '{0}'.format(start),
            '{0}'.format(end),
            [
                '{',
                '"title": "{0}",'.format(enrich.title),
                '"type": "{0}",'.format(enrich.type),
                '"url": "{0}"'.format(url),
                '}'
            ]
        )
        caption.identifier = enrich.slug
        webvtt.captions.append(caption)
        base_dir = None
    if AUTH:
        base_dir = Owner.objects.get(id=video.owner.id).hashkey
    else:
        base_dir = video.owner.username
    file_path = os.path.join(
        settings.MEDIA_ROOT,
        'files',
        base_dir,
        'Home',
        'enrich_{0}.vtt'.format(video.title))
    webvtt.save(file_path)
    file = File(open(file_path))
    file.name = 'enrich_{0}.vtt'.format(video.title)
    if FILEPICKER:
        home = UserDirectory.objects.get(
            owner=video.owner, name='Home')
        CustomFileModel.objects.filter(
            name='enrich_{0}'.format(video.title),
            created_by=video.owner,
            directory=home).delete()
        new = CustomFileModel.objects.create(
            name='enrich_{0}'.format(video.title),
            file_size=os.path.getsize(file_path),
            file_type='VTT',
            date_created=timezone.now(),
            date_modified=timezone.now(),
            created_by=video.owner,
            modified_by=video.owner,
            directory=home,
            file=file)
        os.remove(file_path)
        path = os.path.join(
            settings.MEDIA_URL,
            new.file.name)
    else:
        path = os.path.join(
            settings.MEDIA_URL,
            'files',
            base_dir,
            'Home',
            file.name)

    return path
