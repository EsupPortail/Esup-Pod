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


def clean_duplicated_UserFolders(dry_run: bool) -> int:
    """Remove duplicated UserFolders and return amount of video with duplicate folders."""
    print("\nCleaning duplicated UserFolders...")
    videos = Video.objects.all()
    nb_duplicated = 0
    for vid in videos:
        # First, we search for Userfolders associated to current vid
        slugid = "%04d-" % vid.id
        videodirs = UserFolder.objects.filter(name__startswith=slugid)
        found = videodirs.all().count()

        if found > 1:
            # Only one folder is needed by video
            print("# More than one Userfolder found for vid %s (%s)." % (slugid, found))
            # We arbitrary keep the first folder.
            primary_folder = videodirs.first()
            print(
                "Primary folder %s `%s` had %s files"
                % (primary_folder.id, primary_folder, len(primary_folder.get_all_files()))
            )
            for folder in list(videodirs.all())[1:]:
                print(
                    " + Add %s files from folder %s `%s`"
                    % (len(folder.get_all_files()), folder.id, folder)
                )
                # Move every file to the primary folder
                if not dry_run:
                    for file in folder.get_all_files():
                        file.folder = primary_folder
                        file.save()
                print(" - Deleting folder %s `%s`" % (folder.id, folder))
                # Delete the duplicated folder
                nb_duplicated += 1
                if not dry_run:
                    folder.delete()
            print(
                "Primary folder %s `%s` has now %s files\n"
                % (primary_folder.id, primary_folder, len(primary_folder.get_all_files()))
            )
    return nb_duplicated


def update_folder_rights(vid: Video, folder: UserFolder) -> int:
    """Update owner rights on specified userFolder."""
    folder_updated = 0
    # Check number of folder users
    folder_users = folder.users.all()
    before = folder_users.count()

    add_own = vid.additional_owners.all()
    expected = add_own.count()
    print("* Regular folder: %s; %s; %s/%s" % (folder.id, folder, before, expected))
    # Update it’s additional owners
    vid.update_additional_owners_rights()

    if expected != before:
        print(" => folder %s updated %s." % (folder, list(folder.users.all())))
        folder_updated = 1
    return folder_updated


class Command(BaseCommand):
    """Delete useless video files."""

    help = "Delete useless files (video or userfolder not associated with a video Object)"

    def add_arguments(self, parser) -> None:
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

    def handle(self, *args, **options) -> None:
        """Handle the clean_video_files command call."""
        if options["dry"]:
            print("Simulation mode ('dry'). Nothing will be deleted.")
        clean_type = options["type"].lower()
        self.nb_deleted = {}
        if clean_type in ["userfolder", "all"]:
            if USE_PODFILE:
                self.nb_deleted["userfolder"] = clean_duplicated_UserFolders(
                    options["dry"]
                )
                if self.nb_deleted["userfolder"] == 0:
                    print("  No duplicated UserFolders found.")
                self.nb_deleted["userfolder"] += self.clean_userFolders(options["dry"])

        if clean_type in ["video", "all"]:
            self.nb_deleted["video"] = self.clean_videos(options["dry"])

        self.print_resume(clean_type, options["dry"])

    def clean_userFolders(self, dry_run: bool) -> int:
        """Clean useless User folders."""
        folder_deleted = 0
        folder_updated = 0
        files_deleted = 0

        print("Start cleaning useless User folders, please wait…")
        user_folders = UserFolder.objects.all()
        for folder in user_folders:
            if "-" in folder.name:
                folder_data = folder.name.split("-")
                if folder_data[0].isdigit():
                    vid_id = int(folder_data[0])
                    try:
                        vid = Video.objects.get(id=vid_id)
                        folder_updated += update_folder_rights(vid, folder)

                    except Video.DoesNotExist:
                        folder_content = folder.get_all_files()
                        print(
                            "* Orphaned folder: %s; %s; %s"
                            % (folder, folder_content, len(folder_content))
                        )
                        folder_deleted += 1
                        files_deleted += len(folder_content)
                        if not dry_run:
                            folder.delete()
        print("Cleaning useless User folders done. %s deleted files." % files_deleted)
        print("%s User folders were updated (owner rights)." % folder_updated)
        return folder_deleted

    def clean_videos(self, dry_run: bool) -> int:
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

    def print_resume(self, clean_type: str, dry_run: bool) -> None:
        """Print summary of deleted files."""
        if clean_type in ["userfolder", "all"]:
            if USE_PODFILE:
                if dry_run:
                    print(
                        "[DRY RUN] %i useless video folder(s) would have been deleted."
                        % (self.nb_deleted["userfolder"])
                    )
                else:
                    print(
                        "%i useless video folder(s) deleted."
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
