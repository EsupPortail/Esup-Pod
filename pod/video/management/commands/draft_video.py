from django.core.management.base import BaseCommand,CommandError
from pod.video.models import Channel,Video

class Command(BaseCommand):
    help="Modifyvideotodraftstatus"

    def add_arguments(self,parser):
        parser.add_argument(
            "id",
            type=int,
            help="Theidofthechannel",
        )

    def handle(self,*args,**options):
        self.stdout.write("%s"%options["id"])
        videos=Video.objects.all().filter(
            channel=Channel.objects.get(id=options["id"])
        )
        self.stdout.write("%s"%videos.count())
        for video in videos:
            self.stdout.write(video.title)
            video.is_draft=True
            video.save()
