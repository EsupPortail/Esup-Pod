"""Script supprimant des fichiers vidéos devenus inutiles."""

from django.core.management.base import BaseCommand
from pod.video.models import Video
from django.conf import settings
from os import listdir, remove
from os.path import isfile, join

USE_PODFILE = getattr(settings, "USE_PODFILE", False)
if USE_PODFILE:
    from pod.podfile.models import UserFolder

VIDEOS_DIR = getattr(settings, "VIDEOS_DIR", "videos")


class Command(BaseCommand):
    """Delete useless video files."""

    help = "Delete useless files (video or userfolder not associated with a video Object)"

    def add_arguments(self, parser):
        """Allow arguments to be used with the command."""
        parser.add_argument(
            "--type",
            default="video",
            help="Type of objects to be deleted.",
            choices=["userfolder", "video", "all"],
            type=str,
        )
        parser.add_argument(
            "--dry",
            help="Simulate what would be deleted.",
            action="store_true",
            default=False,
        )

    def handle(self, *args, **options):
        """Handle the clean_video_files command call."""
        if options["dry"]:
            print("Simulation mode ('dry'). Nothing will be deleted.")
        clean_type = options["type"].lower()
        self.nb_deleted = {}
        if clean_type in ["userfolder", "all"]:
            if USE_PODFILE:
                self.nb_deleted["userfolder"] = self.clean_userFolders(options["dry"])

        if clean_type in ["video", "all"]:
            self.nb_deleted["video"] = self.clean_videos(options["dry"])

        self.print_resume(clean_type, options["dry"])

    def clean_userFolders(self, dry_run):
        """Clean useless User folders."""
        folder_deleted = 0
        files_deleted = 0

        print("Start cleaning useless User folders, please wait...")
        user_folders = UserFolder.objects.all()
        for folder in user_folders:
            if "-" in folder.name:
                folder_data = folder.name.split("-")
                if folder_data[0].isdigit():
                    vid_id = int(folder_data[0])
                    try:
                        Video.objects.get(id=vid_id)
                    except Video.DoesNotExist:
                        folder_content = folder.get_all_files()
                        print("%s;%s;%s" % (folder, folder_content, len(folder_content)))
                        folder_deleted += 1
                        files_deleted += len(folder_content)
                        if not dry_run:
                            folder.delete()
        print("Cleaning useless User folders done. %s deleted files." % files_deleted)
        return folder_deleted

    def clean_videos(self, dry_run):
        """Clean useless video files."""
        list_dir = listdir(join(settings.MEDIA_ROOT, VIDEOS_DIR))
        print("Start cleaning useless video files, please wait...")
        nb_deleted = 0
        for video_dir in list_dir:
            mypath = join(settings.MEDIA_ROOT, VIDEOS_DIR, video_dir)
            onlyfiles = [f for f in listdir(mypath) if isfile(join(mypath, f))]
            for myfile in onlyfiles:
                try:
                    Video.objects.get(video="%s/%s/%s" % (VIDEOS_DIR, video_dir, myfile))
                except Video.DoesNotExist:
                    vid_path = join(settings.MEDIA_ROOT, VIDEOS_DIR, video_dir, myfile)
                    print(vid_path)
                    nb_deleted += 1
                    if not dry_run:
                        remove(vid_path)
        print("Cleaning useless video files done.")
        return nb_deleted

    def print_resume(self, clean_type, dry_run):
        """Print summary of deleted files."""
        if clean_type in ["userfolder", "all"]:
            if USE_PODFILE:
                if dry_run:
                    print(
                        "[DRY RUN] %i useless user folders would have been deleted."
                        % (self.nb_deleted["userfolder"])
                    )
                else:
                    print(
                        "%i useless video folders deleted."
                        % (self.nb_deleted["userfolder"])
                    )
            else:
                print("No need to clean User Folders, as USE_PODFILE = False...")
        if clean_type in ["video", "all"]:
            if dry_run:
                print(
                    "[DRY RUN] %i useless video files would have been deleted."
                    % (self.nb_deleted["video"])
                )
            else:
                print("%i useless video files deleted." % self.nb_deleted["video"])
        print("Have a nice day ;)")
