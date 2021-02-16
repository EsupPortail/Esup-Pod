from django.core.management.base import BaseCommand
from pod.video.models import Video
from django.contrib.auth.models import User
from django.core.exceptions import ObjectDoesNotExist


class Command(BaseCommand):
    help = 'Unarchive a video'

    def add_arguments(self, parser):
        parser.add_argument('video_id', type=int, help='Video id')
        parser.add_argument('user_id', type=int, help='Video id')

    def handle(self, *args, **options):
        video = 1
        user = 1
        try:
            video = Video.objects.get(id=options['video_id'])
        except ObjectDoesNotExist:
            self.stdout.write(self.style.ERROR(
                'Video not found "%s"' % options['video_id']))
            return
        try:
            user = User.objects.get(id=options['user_id'])
        except ObjectDoesNotExist:
            self.stdout.write(self.style.ERROR(
                'User not found "%s"' % options['user_id']))
            return

        video.owner = user
        video.save()
        self.stdout.write(self.style.SUCCESS(
            'Video "%s" has been unarchived' % video.id))
