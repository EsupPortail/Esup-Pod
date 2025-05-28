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
    python manage.py check_database_data
Arguments:
 --dry: Simulates what will be achieved (default=False).

Example: python manage.py check_database_data --dry

Functions:
- add_arguments: Adds command-line arguments for the script.
- handle: Main entry point for the command, handling the overall process.
- process: Core method that orchestrates the database verification for all videos.
- check_change_owner_problems: Detects if a video's encoding paths do not match the current owner's hashkey.
- solve_change_owner_problems: Corrects file paths in EncodingVideo, EncodingAudio, and PlaylistVideo models to match the new owner.
"""
import re

from django.core.management.base import BaseCommand
from pod.video.models import Video
from pod.video_encode_transcript.models import EncodingVideo, EncodingAudio
from pod.video_encode_transcript.models import PlaylistVideo
from typing import Any, Dict


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

    def handle(self, *args: Any, **options: Any) -> None:
        """Handle the command call."""

        self.stdout.write(
            self.style.SUCCESS("***Start check database consistency***")
        )

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

    def process(self, options: Dict[str, Any]) -> None:
        """Main process to check database data."""

        # Check all videos
        videos = Video.objects.filter()
        for video in videos:
            # Step 1: check problems in video_encode_transcript_* tables
            # Problem due to change of video owner in the Pod administration
            self.check_change_owner_problems(video, options)
        if self.nb_errors_found == 0:
            self.stdout.write(
                self.style.SUCCESS("No problems found in connection with the change of ownership.")
            )

    def check_change_owner_problems(self, video: Video, options: Dict[str, Any]) -> None:
        """Checks for problems in the database relating to changes of ownership."""

        # Try to identify the problem for this video
        encodings_video = EncodingVideo.objects.filter(video=video)
        if encodings_video:
            encoding_video = encodings_video[0]
            if encoding_video.source_file.name.find(video.owner.owner.hashkey) == -1:
                self.nb_errors_found += 1
                # Problem found for a video
                if options["dry"]:
                    if self.nb_errors_found == 1:
                        self.stdout.write(
                            self.style.WARNING(
                                "Problems found:\n"
                                "VIDEO ID; TYPE; DETAIL"
                            )
                        )
                    self.stdout.write(
                        self.style.WARNING(
                            f"{video.id}; change of owner;  "
                            f"encoding {encoding_video.source_file.name} not in "
                            f"{video.owner.owner.hashkey} folder."
                        )
                    )
                else:
                    self.solve_change_owner_problems(video)

    def solve_change_owner_problems(self, video: Video) -> None:
        """Solves problems in the database relating to changes of ownership."""
        # Change the path of encodings related to a video
        models_to_update = [EncodingVideo, EncodingAudio, PlaylistVideo]
        for model in models_to_update:
            encodings = model.objects.filter(video=video)
            for encoding in encodings:
                encoding.source_file = re.sub(
                    r"\w{64}", video.owner.owner.hashkey, encoding.source_file.name.__str__()
                )
                encoding.save()
        self.stdout.write(
            self.style.SUCCESS(f"Owner change: problem identified and solved for video {video.id}.")
        )
