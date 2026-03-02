"""Utilities for storing and importing remote encoding artifacts in Esup-Pod.

This module orchestrates post-encoding persistence for videos and recordings:
- updates encoding logs and processing state,
- imports generated files (video/audio/playlist/thumbnail),
- clears stale artifacts from previous runs.
"""

import json
import logging
import os
import re
import time
from typing import Any, TypedDict, cast

from django.conf import settings
from django.core.files import File
from webpush.models import PushInformation

from pod.recorder.models import Recording
from pod.video.models import Video

from .models import (
    EncodingAudio,
    EncodingLog,
    EncodingVideo,
    PlaylistVideo,
    VideoRendition,
)
from .utils import (
    add_encoding_log,
    change_encoding_step,
    check_file,
    create_outputdir,
    send_email,
    send_email_encoding,
    send_notification_encoding,
)

if getattr(settings, "USE_PODFILE", False):
    FILEPICKER = True
    from pod.podfile.models import CustomImageModel
else:
    FILEPICKER = False
    from pod.main.models import CustomImageModel

log = logging.getLogger(__name__)

DEBUG = getattr(settings, "DEBUG", True)

USE_NOTIFICATIONS = getattr(settings, "USE_NOTIFICATIONS", True)

USE_TRANSCRIPTION = getattr(settings, "USE_TRANSCRIPTION", False)

if USE_TRANSCRIPTION:
    from . import transcript

    TRANSCRIPT_VIDEO = getattr(settings, "TRANSCRIPT_VIDEO", "start_transcript")

EMAIL_ON_ENCODING_COMPLETION = getattr(settings, "EMAIL_ON_ENCODING_COMPLETION", True)

ENCODING_CHOICES = getattr(
    settings,
    "ENCODING_CHOICES",
    (
        ("audio", "audio"),
        ("360p", "360p"),
        ("480p", "480p"),
        ("720p", "720p"),
        ("1080p", "1080p"),
        ("playlist", "playlist"),
    ),
)


class EncodedAudioInfo(TypedDict):
    """Audio entry produced by the remote encoder."""

    encoding_format: str
    filename: str


class EncodedVideoInfo(TypedDict):
    """Video entry produced by the remote encoder."""

    encoding_format: str
    filename: str
    rendition: str


class EncodedThumbnailInfo(TypedDict):
    """Thumbnail entry produced by the remote encoder."""

    filename: str


class RemoteEncodingInfo(TypedDict, total=False):
    """Top-level JSON payload written by the remote encoder."""

    duration: float
    has_stream_video: bool
    has_stream_audio: bool
    has_stream_thumbnail: bool
    encode_video: list[EncodedVideoInfo]
    encode_audio: EncodedAudioInfo | list[EncodedAudioInfo]
    encode_thumbnail: EncodedThumbnailInfo | list[EncodedThumbnailInfo]


def store_before_remote_encoding_recording(
    recording_id: int, execute_url: str, data: dict[str, Any]
) -> None:
    """Store pre-encoding metadata for a recording."""
    recording = Recording.objects.get(id=recording_id)
    msg = "\nStart at: %s" % time.ctime()
    msg += "\nprocess manager remote encode: %s with data %s" % (execute_url, data)
    recording.comment += msg
    recording.save()


def store_remote_encoding_log_recording(recording_id: int, video_id: int) -> None:
    # Get recording info
    recording = Recording.objects.get(id=recording_id)
    # Get video info
    video_to_encode = Video.objects.get(id=video_id)
    # Store encoding log
    encoding_log, created = EncodingLog.objects.get_or_create(video=video_to_encode)
    encoding_log.log = "%s" % recording.comment
    encoding_log.save()


def store_before_remote_encoding_video(
    video_id: int, execute_url: str, data: dict[str, Any]
) -> None:
    """Initialize video state and logs before remote encoding starts."""
    start = "Start at: %s" % time.ctime()
    msg = ""
    video_to_encode = Video.objects.get(id=video_id)
    video_to_encode.encoding_in_progress = True
    video_to_encode.save()
    change_encoding_step(video_id, 0, "start")

    encoding_log, created = EncodingLog.objects.get_or_create(video=video_to_encode)
    encoding_log.log = "%s" % start
    encoding_log.save()

    if check_file(video_to_encode.video.path):
        change_encoding_step(video_id, 1, "remove old data")
        remove_msg = remove_old_data(video_id)
        add_encoding_log(video_id, "remove old data: %s" % remove_msg)

        change_encoding_step(video_id, 2, "create output dir")
        output_dir = create_outputdir(video_id, video_to_encode.video.path)
        add_encoding_log(video_id, "output_dir: %s" % output_dir)

        open(output_dir + "/encoding.log", "w").close()
        with open(output_dir + "/encoding.log", "a") as f:
            f.write("%s\n" % start)

        change_encoding_step(video_id, 3, "process manager remote encode")
        add_encoding_log(
            video_id,
            "process manager remote encode: %s with data %s" % (execute_url, data),
        )

    else:
        msg += "Wrong file or path: " + "\n%s" % video_to_encode.video.path
        add_encoding_log(video_id, msg)
        change_encoding_step(video_id, -1, msg)
        send_email(msg, video_id)


def store_after_remote_encoding_video(video_id: int) -> None:
    """Import remote artifacts and finalize encoding state for a video."""
    msg = ""
    video_to_encode = Video.objects.get(id=video_id)
    output_dir = create_outputdir(video_id, video_to_encode.video.path)
    info_video: RemoteEncodingInfo = {}

    with open(output_dir + "/info_video.json", encoding="utf-8") as json_file:
        info_video = cast(RemoteEncodingInfo, json.load(json_file))

    video_to_encode.duration = info_video["duration"]
    video_to_encode.encoding_in_progress = True
    video_to_encode.save()

    msg += remote_video_part(video_to_encode, info_video, output_dir)
    msg += remote_audio_part(video_to_encode, info_video, output_dir)

    video_encoding = Video.objects.get(id=video_id)

    if not info_video["has_stream_video"]:
        video_encoding.is_video = False
        video_encoding.save()

    add_encoding_log(video_id, msg)
    change_encoding_step(video_id, 0, "done")

    video_encoding.encoding_in_progress = False
    video_encoding.save()

    add_encoding_log(video_id, "End: %s" % time.ctime())
    with open(output_dir + "/encoding.log", "a") as f:
        f.write("\n\nEnd: %s" % time.ctime())

    if (
        USE_NOTIFICATIONS
        and video_encoding.owner.owner.accepts_notifications
        and PushInformation.objects.filter(user=video_encoding.owner).exists()
    ):
        send_notification_encoding(video_encoding)

    if EMAIL_ON_ENCODING_COMPLETION:
        send_email_encoding(video_encoding)

    if USE_TRANSCRIPTION and video_encoding.transcript not in ["", "0", "1"]:
        start_transcript_video = getattr(transcript, TRANSCRIPT_VIDEO)
        log.info(
            "Start transcript video %s",
            getattr(transcript, TRANSCRIPT_VIDEO),
        )
        start_transcript_video(video_id, False)

    log.info("ALL is DONE")


def remote_audio_part(
    video_to_encode: Video, info_video: RemoteEncodingInfo, output_dir: str
) -> str:
    """Import audio (and optional thumbnail) artifacts from remote outputs."""
    msg = ""
    if info_video["has_stream_audio"] and info_video.get("encode_audio"):
        msg += import_remote_audio(
            info_video["encode_audio"], output_dir, video_to_encode
        )
        # Avoid importing the same thumbnail twice when both audio and video are present.
        if (
            info_video["has_stream_thumbnail"]
            and info_video.get("encode_thumbnail")
            and not (
                info_video.get("has_stream_video", False)
                and info_video.get("encode_video")
            )
        ):
            msg += import_remote_thumbnail(
                info_video["encode_thumbnail"], output_dir, video_to_encode
            )
    elif info_video["has_stream_audio"] or info_video.get("encode_audio"):
        msg += "\n- has stream audio but not info audio in json "
        add_encoding_log(video_to_encode.id, msg)
        change_encoding_step(video_to_encode.id, -1, msg)
        send_email(msg, video_to_encode.id)
    return msg


def remote_video_part(
    video_to_encode: Video, info_video: RemoteEncodingInfo, output_dir: str
) -> str:
    """Import video artifacts and attach optional overview/thumbnail files."""
    msg = ""
    if info_video["has_stream_video"] and info_video.get("encode_video"):
        msg += import_remote_video(
            info_video["encode_video"], output_dir, video_to_encode
        )
        video_id = video_to_encode.id
        # If the remote pipeline generated overview thumbnails metadata, attach it.
        overview_vtt = os.path.join(output_dir, "overview.vtt")
        if check_file(overview_vtt):
            try:
                video_to_encode.overview = overview_vtt.replace(
                    os.path.join(settings.MEDIA_ROOT, ""), ""
                )
                video_to_encode.save()
                msg += "\n- existing overview:\n%s" % overview_vtt
                add_encoding_log(
                    video_id, "attach existing overview: %s" % overview_vtt
                )
            except Exception as err:
                err_msg = f"Error attaching existing overview: {err}"
                add_encoding_log(video_id, err_msg)
        else:
            add_encoding_log(video_id, "No existing overview file found (overview.vtt)")

        if info_video["has_stream_thumbnail"] and info_video.get("encode_thumbnail"):
            msg += import_remote_thumbnail(
                info_video["encode_thumbnail"], output_dir, video_to_encode
            )
        else:
            add_encoding_log(
                video_id, "No thumbnail info in json; skip thumbnail attach"
            )
    elif info_video["has_stream_video"] or info_video.get("encode_video"):
        msg += "\n- has stream video but not info video "
        add_encoding_log(video_to_encode.id, msg)
        change_encoding_step(video_to_encode.id, -1, msg)
        send_email(msg, video_to_encode.id)

    return msg


def _get_ordered_thumbnail_entries(
    info_encode_thumbnail: EncodedThumbnailInfo | list[EncodedThumbnailInfo],
) -> list[EncodedThumbnailInfo]:
    """Return thumbnail entries with the preferred (middle) candidate first."""
    # Accept both a single thumbnail payload and a list from different callers.
    thumbnail_entries: list[EncodedThumbnailInfo]
    if isinstance(info_encode_thumbnail, list):
        thumbnail_entries = info_encode_thumbnail
    else:
        thumbnail_entries = [info_encode_thumbnail]

    if not thumbnail_entries:
        return []

    # Build sortable tuples: (numeric filename suffix, original position, payload).
    # Example matched suffix: "thumb_2.png" -> 2.
    indexed_entries: list[tuple[int | None, int, EncodedThumbnailInfo]] = []
    for position, thumbnail_data in enumerate(thumbnail_entries):
        filename = thumbnail_data.get("filename", "")
        match = re.search(r"_(\d+)(?=\.[^.]+$)", os.path.basename(filename))
        index = int(match.group(1)) if match else None
        indexed_entries.append((index, position, thumbnail_data))

    has_numeric_indexes = any(entry[0] is not None for entry in indexed_entries)
    if has_numeric_indexes:
        # Keep numerically indexed files first (ordered by index), then fallback entries
        # without index in their original input order.
        thumbnail_entries = [
            entry[2]
            for entry in sorted(
                indexed_entries,
                key=lambda item: (
                    item[0] is None,
                    item[0] if item[0] is not None else item[1],
                ),
            )
        ]

    # Move the middle candidate to the first position as the preferred thumbnail.
    preferred_index = len(thumbnail_entries) // 2
    ordered_entries = [thumbnail_entries[preferred_index]]
    ordered_entries.extend(
        thumbnail_data
        for pos, thumbnail_data in enumerate(thumbnail_entries)
        if pos != preferred_index
    )
    return ordered_entries


def _save_thumbnail_for_video(
    video_to_encode: Video,
    thumbnailfilename: str,
    thumbnail_name: str,
) -> CustomImageModel:
    """Persist one thumbnail file and return the stored image object."""
    if FILEPICKER:
        videodir = video_to_encode.get_or_create_video_folder()
        thumbnail = CustomImageModel(folder=videodir, created_by=video_to_encode.owner)
    else:
        thumbnail = CustomImageModel()
    with open(thumbnailfilename, "rb") as thumbnail_file:
        thumbnail.file.save(
            thumbnail_name,
            File(thumbnail_file),
            save=True,
        )
    thumbnail.save()
    return thumbnail


def import_remote_thumbnail(
    info_encode_thumbnail: EncodedThumbnailInfo | list[EncodedThumbnailInfo],
    output_dir: str,
    video_to_encode: Video,
) -> str:
    """Import all generated thumbnails and associate one preferred thumbnail to the video."""
    msg = ""
    ordered_thumbnails = _get_ordered_thumbnail_entries(info_encode_thumbnail)
    if not ordered_thumbnails:
        msg += "\nERROR THUMBNAILS missing data "
        add_encoding_log(video_to_encode.id, msg)
        change_encoding_step(video_to_encode.id, -1, msg)
        send_email(msg, video_to_encode.id)
        return msg

    checked_thumbnail_files: list[str] = []
    selected_thumbnail: CustomImageModel | None = None
    for thumbnail_data in ordered_thumbnails:
        thumbnail_name = thumbnail_data.get("filename")
        if not thumbnail_name:
            continue

        thumbnailfilename = os.path.join(output_dir, thumbnail_name)
        checked_thumbnail_files.append(thumbnailfilename)
        if not check_file(thumbnailfilename):
            continue

        stored_thumbnail = _save_thumbnail_for_video(
            video_to_encode,
            thumbnailfilename,
            thumbnail_name,
        )
        if selected_thumbnail is None:
            selected_thumbnail = stored_thumbnail
        msg += "\n- thumbnailfilename:\n%s" % thumbnailfilename

    if selected_thumbnail is not None:
        video_to_encode.thumbnail = selected_thumbnail
        video_to_encode.save()
        return msg

    missing_files = ", ".join(checked_thumbnail_files) or "missing data"
    msg += "\nERROR THUMBNAILS %s " % missing_files
    msg += "Wrong file or path"
    add_encoding_log(video_to_encode.id, msg)
    change_encoding_step(video_to_encode.id, -1, msg)
    send_email(msg, video_to_encode.id)
    return msg


def import_remote_audio(
    info_encode_audio: EncodedAudioInfo | list[EncodedAudioInfo],
    output_dir: str,
    video_to_encode: Video,
) -> str:
    """Persist generated audio tracks (mp3/m4a) for a video."""
    msg = ""
    if isinstance(info_encode_audio, dict):
        info_encode_audio = [info_encode_audio]
    for encode_audio in info_encode_audio:
        if encode_audio["encoding_format"] == "audio/mp3":
            filename = os.path.splitext(encode_audio["filename"])[0]
            audiofilename = os.path.join(output_dir, "%s.mp3" % filename)
            if check_file(audiofilename):
                encoding, created = EncodingAudio.objects.get_or_create(
                    name="audio",
                    video=video_to_encode,
                    encoding_format="audio/mp3",
                )
                encoding.source_file = audiofilename.replace(
                    os.path.join(settings.MEDIA_ROOT, ""), ""
                )
                encoding.save()
                msg += "\n- encode_video_mp3:\n%s" % audiofilename
            else:
                msg += "\n- encode_video_mp3 Wrong file or path "
                msg += audiofilename + " "
                add_encoding_log(video_to_encode.id, msg)
                change_encoding_step(video_to_encode.id, -1, msg)
                send_email(msg, video_to_encode.id)
        if encode_audio["encoding_format"] == "video/mp4":
            filename = os.path.splitext(encode_audio["filename"])[0]
            audiofilename = os.path.join(output_dir, "%s.m4a" % filename)
            if check_file(audiofilename):
                encoding, created = EncodingAudio.objects.get_or_create(
                    name="audio",
                    video=video_to_encode,
                    encoding_format="video/mp4",
                )
                encoding.source_file = audiofilename.replace(
                    os.path.join(settings.MEDIA_ROOT, ""), ""
                )
                encoding.save()
                msg += "\n- encode_video_m4a:\n%s" % audiofilename
            else:
                msg += "\n- encode_video_m4a Wrong file or path "
                msg += audiofilename + " "
                add_encoding_log(video_to_encode.id, msg)
                change_encoding_step(video_to_encode.id, -1, msg)
                send_email(msg, video_to_encode.id)
    return msg


def import_remote_video(
    info_encode_video: list[EncodedVideoInfo],
    output_dir: str,
    video_to_encode: Video,
) -> str:
    """Persist generated video tracks and build the HLS master playlist."""
    msg = ""
    master_playlist = ""
    video_has_playlist = False
    for encod_video in info_encode_video:
        if encod_video["encoding_format"] == "video/mp2t":
            video_has_playlist = True
            import_msg, import_master_playlist = import_m3u8(
                encod_video, output_dir, video_to_encode
            )
            msg += import_msg
            master_playlist += import_master_playlist

        if encod_video["encoding_format"] == "video/mp4":
            import_msg = import_mp4(encod_video, output_dir, video_to_encode)
            msg += import_msg

    if video_has_playlist:
        # Aggregate all rendition playlists into a single HLS master playlist.
        playlist_master_file = output_dir + "/playlist.m3u8"
        with open(playlist_master_file, "w") as f:
            f.write("#EXTM3U\n#EXT-X-VERSION:3\n" + master_playlist)

        if check_file(playlist_master_file):
            playlist, created = PlaylistVideo.objects.get_or_create(
                name="playlist",
                video=video_to_encode,
                encoding_format="application/x-mpegURL",
            )
            playlist.source_file = (
                output_dir.replace(os.path.join(settings.MEDIA_ROOT, ""), "")
                + "/playlist.m3u8"
            )
            playlist.save()

            msg += "\n- Playlist:\n%s" % playlist_master_file
        else:
            msg = (
                "save_playlist_master Wrong file or path: "
                + "\n%s" % playlist_master_file
            )
            add_encoding_log(video_to_encode.id, msg)
            change_encoding_step(video_to_encode.id, -1, msg)
            send_email(msg, video_to_encode.id)
    return msg


def import_mp4(
    encod_video: EncodedVideoInfo, output_dir: str, video_to_encode: Video
) -> str:
    """Persist a single MP4 rendition into EncodingVideo."""
    filename = os.path.splitext(encod_video["filename"])[0]
    videofilenameMp4 = os.path.join(output_dir, "%s.mp4" % filename)
    msg = "\n- videofilenameMp4:\n%s" % videofilenameMp4
    if check_file(videofilenameMp4):
        rendition = VideoRendition.objects.get(resolution=encod_video["rendition"])
        encoding, created = EncodingVideo.objects.get_or_create(
            name=get_encoding_choice_from_filename(filename),
            video=video_to_encode,
            rendition=rendition,
            encoding_format="video/mp4",
        )
        encoding.source_file = videofilenameMp4.replace(
            os.path.join(settings.MEDIA_ROOT, ""), ""
        )
        encoding.save()
    else:
        msg = "save_mp4_file Wrong file or path: " + "\n%s " % (videofilenameMp4)
        add_encoding_log(video_to_encode.id, msg)
        change_encoding_step(video_to_encode.id, -1, msg)
        send_email(msg, video_to_encode.id)
    return msg


def import_m3u8(
    encod_video: EncodedVideoInfo, output_dir: str, video_to_encode: Video
) -> tuple[str, str]:
    """Persist one HLS rendition and return its master playlist fragment."""
    msg = ""
    master_playlist = ""
    filename = os.path.splitext(encod_video["filename"])[0]
    videofilenameM3u8 = os.path.join(output_dir, "%s.m3u8" % filename)
    videofilenameTS = os.path.join(output_dir, "%s.ts" % filename)
    msg += "\n- videofilenameM3u8:\n%s" % videofilenameM3u8
    msg += "\n- videofilenameTS:\n%s" % videofilenameTS

    rendition = VideoRendition.objects.get(resolution=encod_video["rendition"])

    bitrate_match = re.search(r"(\d+)k", rendition.video_bitrate, re.I)
    if bitrate_match is None:
        msg = "Invalid rendition bitrate format: %s" % rendition.video_bitrate
        add_encoding_log(video_to_encode.id, msg)
        change_encoding_step(video_to_encode.id, -1, msg)
        send_email(msg, video_to_encode.id)
        return msg, master_playlist

    int_bitrate = int(bitrate_match.group(1))
    bandwidth = int_bitrate * 1000

    if check_file(videofilenameM3u8) and check_file(videofilenameTS):
        encoding, created = EncodingVideo.objects.get_or_create(
            name=get_encoding_choice_from_filename(filename),
            video=video_to_encode,
            rendition=rendition,
            encoding_format="video/mp2t",
        )
        encoding.source_file = videofilenameTS.replace(
            os.path.join(settings.MEDIA_ROOT, ""), ""
        )
        encoding.save()

        playlist, created = PlaylistVideo.objects.get_or_create(
            name=get_encoding_choice_from_filename(filename),
            video=video_to_encode,
            encoding_format="application/x-mpegURL",
        )
        playlist.source_file = videofilenameM3u8.replace(
            os.path.join(settings.MEDIA_ROOT, ""), ""
        )
        playlist.save()

        master_playlist += "#EXT-X-STREAM-INF:BANDWIDTH=%s," % bandwidth
        master_playlist += "RESOLUTION=%s\n%s\n" % (
            rendition.resolution,
            encod_video["filename"],
        )
    else:
        msg = "save_playlist_file Wrong file or path: " + "\n%s and %s" % (
            videofilenameM3u8,
            videofilenameTS,
        )
        add_encoding_log(video_to_encode.id, msg)
        change_encoding_step(video_to_encode.id, -1, msg)
        send_email(msg, video_to_encode.id)

    return msg, master_playlist


def get_encoding_choice_from_filename(filename: str) -> str:
    """Map filename prefix to the configured encoding choice name."""
    choices: dict[str, str] = {}
    for choice in ENCODING_CHOICES:
        choices[choice[0][:3]] = choice[0]
    return choices.get(filename[:3], "360p")


def remove_old_data(video_id: int) -> str:
    """Remove old data."""
    video_to_encode = Video.objects.get(id=video_id)
    video_to_encode.thumbnail = None
    if video_to_encode.overview:
        image_overview = os.path.join(
            os.path.dirname(video_to_encode.overview.path), "overview.png"
        )
        if os.path.isfile(image_overview):
            os.remove(image_overview)
        video_to_encode.overview.delete()
    video_to_encode.overview = None
    video_to_encode.save()

    encoding_log_msg = ""
    encoding_log_msg += remove_previous_encoding_video(video_to_encode)
    encoding_log_msg += remove_previous_encoding_audio(video_to_encode)
    encoding_log_msg += remove_previous_encoding_playlist(video_to_encode)
    return encoding_log_msg


def remove_previous_encoding_video(video_to_encode: Video) -> str:
    """Remove previously encoded video."""
    msg = "\n"
    previous_encoding_video = EncodingVideo.objects.filter(video=video_to_encode)
    if len(previous_encoding_video) > 0:
        msg += "\nDELETE PREVIOUS ENCODING VIDEO"
        for encoding in previous_encoding_video:
            encoding.delete()
    else:
        msg += "Video: Nothing to delete"
    return msg


def remove_previous_encoding_audio(video_to_encode: Video) -> str:
    """Remove previously encoded audio."""
    msg = "\n"
    previous_encoding_audio = EncodingAudio.objects.filter(video=video_to_encode)
    if len(previous_encoding_audio) > 0:
        msg += "\nDELETE PREVIOUS ENCODING AUDIO"
        for encoding in previous_encoding_audio:
            encoding.delete()
    else:
        msg += "Audio: Nothing to delete"
    return msg


def remove_previous_encoding_playlist(video_to_encode: Video) -> str:
    """Remove previously encoded playlist."""
    msg = "\n"
    previous_playlist = PlaylistVideo.objects.filter(video=video_to_encode)
    if len(previous_playlist) > 0:
        msg += "DELETE PREVIOUS PLAYLIST M3U8"
        for encoding in previous_playlist:
            encoding.delete()
    else:
        msg += "Playlist: Nothing to delete"
    return msg
