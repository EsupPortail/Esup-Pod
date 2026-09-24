"""
Database Consistency Check Script for Esup-Pod.

This script checks for inconsistencies in the database, particularly focusing on issues
that arise when video ownership is changed in the Pod administration interface.
Compatible with v3.8 / v4.

Key Features:
- Identifies encoding files with incorrect owner hashkey references
- Provides a dry-run mode to simulate changes without modifying the database
- Automatically fixes detected ownership path inconsistencies

Main Components:
- Command class: Entry point for Django management command
- Process methods: Handle the main checking and fixing logic
- Owner change detection: Specialized functions to handle ownership-related issues

Important notes:
 - Do not forget to save database (at least video_encode_transcript_* tables) before use.

Usage:
Run the script using Django's management command:
    python manage.py check_database_problems
Arguments:
 --dry: Simulates what will be achieved (default=False).

Example: python manage.py check_database_problems --dry

Functions:
- add_arguments: Adds command-line arguments for the script.
- handle: Main entry point for the command, handling the overall process.
- process: Core method that orchestrates the database verification for all videos.
- check_change_owner_problems: Detects if a video's encoding paths do not match the current owner's hashkey.
- solve_change_owner_problems: Moves/deduplicates encoding files on the filesystem and corrects file paths in
  EncodingVideo, EncodingAudio, and PlaylistVideo models to match the new owner.
"""

import os
import re
import shutil

from django.conf import settings
from django.core.management.base import BaseCommand

from pod.authentication.models import Owner
from pod.video.models import Video
from pod.video_encode_transcript.models import EncodingAudio, EncodingVideo, PlaylistVideo

ARCHIVE_OWNER_USERNAME = getattr(settings, "ARCHIVE_OWNER_USERNAME", "archive")
VIDEOS_DIR = getattr(settings, "VIDEOS_DIR", "videos")


def get_video_dir(hashkey: str, video_id: int) -> str:
    """Get the absolute directory holding a video's encoding files for a given owner hashkey."""
    return os.path.join(settings.MEDIA_ROOT, VIDEOS_DIR, hashkey, str(video_id))

def find_hashkey(video: Video, models_to_update: list):
    """Find the owner hashkey currently set for a video."""
    for model in models_to_update:
        encoding = model.objects.filter(video=video).first()
        if encoding:
            match = re.search(r"\w{64}", encoding.source_file.name)
            if match:
                return match.group(0)
    return None

class Command(BaseCommand):
    """Main command class to check whether the data in the database is inconsistent."""

    nb_errors_found = 0

    help = "Check for problems with database data"

    def add_arguments(self, parser) -> None:
        """Allow arguments to be used with the command."""
        parser.add_argument(
            "--dry",
            help="Simulates what will be achieved (default=False).",
            action="store_true",
            default=False,
        )

    def handle(self, *args, **options) -> None:
        """Handle the command call."""

        self.stdout.write(self.style.SUCCESS("***Start check database consistency***"))

        if options["dry"]:
            self.stdout.write(
                self.style.NOTICE(
                    "\n----------------------------------------------------------------\n"
                    "| Simulation mode ('dry'). No database update, only print info.|"
                    "\n----------------------------------------------------------------\n"
                )
            )

        # Main function
        self.process(options)

    def process(self, options) -> None:
        """Main process to check database data."""

        # Check all videos
        videos = Video.objects.filter()
        for video in videos:
            # Step 1: check problems in video_encode_transcript_* tables
            # Problem due to change of video owner in the Pod administration
            self.check_change_owner_problems(video, options)
        if self.nb_errors_found == 0:
            self.stdout.write(
                self.style.SUCCESS(
                    "No problems found in connection with the change of ownership."
                )
            )

    def check_change_owner_problems(self, video: Video, options) -> None:
        """Checks for problems in the database relating to changes of ownership."""

        # Try to identify the problem for this video
        encodings_video = EncodingVideo.objects.filter(video=video)
        if encodings_video:
            encoding_video = encodings_video[0]
            # Isolate potential hashkey in source_file name
            match = re.search(r"\w{64}", encoding_video.source_file.name)
            if match:
                found_hashkey = match.group(0)
                try:
                    # Search existing user matching this hashkey
                    folder_owner = Owner.objects.get(hashkey=found_hashkey).user.username
                except Owner.DoesNotExist:
                    folder_owner = "unknown"
                if video.owner.username != folder_owner:
                    self.nb_errors_found += 1
                    # Problem found for a video
                    if options["dry"]:
                        if self.nb_errors_found == 1:
                            self.stdout.write(
                                self.style.WARNING(
                                    "Problems found:\n"
                                    "VIDEO ID; PROBLEM TYPE; VID OWNER; FOLDER OWNER ;ACTUAL FILE; EXPECTED FOLDER"
                                )
                            )
                        if video.owner.username == ARCHIVE_OWNER_USERNAME:
                            problem_type = "archived video"
                        else:
                            problem_type = "change of owner"
                        self.stdout.write(
                            self.style.WARNING(
                                f"{video.id}; {problem_type}; "
                                f"{video.owner.username}; {folder_owner}; "
                                f"{encoding_video.source_file.name}; "
                                f"{video.owner.owner.hashkey}"
                            )
                        )
                    else:
                        self.solve_change_owner_problems(video)
            else:
                self.stdout.write(
                    self.style.ERROR(
                        "Impossible to extract hashkey from %s"
                        % encoding_video.source_file.name
                    )
                )


    def move_video_dir_if_needed(
        self, old_hashkey: str, new_hashkey: str, video: Video
    ) -> None:
        """Move the whole video folder to the new owner if it does not already exist there."""
        old_video_dir = get_video_dir(old_hashkey, video.id)
        new_video_dir = get_video_dir(new_hashkey, video.id)
        if os.path.isdir(old_video_dir) and not os.path.isdir(new_video_dir):
            os.makedirs(os.path.dirname(new_video_dir), exist_ok=True)
            shutil.move(old_video_dir, new_video_dir)
            self.stdout.write(
                self.style.SUCCESS(f"Moved folder {old_video_dir} to {new_video_dir}.")
            )

    def move_or_deduplicate_encoding_file(self, encoding, new_hashkey: str) -> None:
        """Make sure a single encoding's file lives in the new owner's folder."""
        old_relative_path = encoding.source_file.name
        new_relative_path = re.sub(r"\w{64}", new_hashkey, old_relative_path)
        old_absolute_path = os.path.join(settings.MEDIA_ROOT, old_relative_path)
        new_absolute_path = os.path.join(settings.MEDIA_ROOT, new_relative_path)

        if os.path.isfile(new_absolute_path):
            if old_absolute_path != new_absolute_path and os.path.isfile(
                old_absolute_path
            ):
                # Duplicate file, removing...
                os.remove(old_absolute_path)
                self.stdout.write(
                    self.style.WARNING(f"Removed duplicate file {old_absolute_path}.")
                )
        elif os.path.isfile(old_absolute_path):
            # File in wring location, moving...
            os.makedirs(os.path.dirname(new_absolute_path), exist_ok=True)
            shutil.move(old_absolute_path, new_absolute_path)
        else:
            # File missing on both sides. Must be re-encoded ?
            self.stdout.write(
                self.style.ERROR(f"File not found on filesystem: {old_absolute_path}")
            )

        encoding.source_file.name = new_relative_path
        encoding.save()

    def solve_change_owner_problems(self, video: Video) -> None:
        """Solves problems in the database and on the filesystem relating to changes of ownership."""
        new_hashkey = video.owner.owner.hashkey
        models_to_update = [EncodingVideo, EncodingAudio, PlaylistVideo]

        old_hashkey = find_hashkey(video, models_to_update)
        if not old_hashkey or old_hashkey == new_hashkey:
            return

        # If the new owner has no folder yet for this video, simply move the whole folder
        self.move_video_dir_if_needed(old_hashkey, new_hashkey, video)

        # Update every encoding record, making sure each file effectively ends up in the
        # new owner's folder, and removing any duplicate left behind by a previous move.
        for model in models_to_update:
            for encoding in model.objects.filter(video=video):
                self.move_or_deduplicate_encoding_file(encoding, new_hashkey)

        self.stdout.write(
            self.style.SUCCESS(
                f"Owner change: problem identified and solved for video {video.id}."
            )
        )
