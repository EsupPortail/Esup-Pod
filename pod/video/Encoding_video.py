from __future__ import absolute_import, division, print_function
import json
import os
import argparse
import time
import unicodedata
from webvtt import WebVTT, Caption

if __name__ == "__main__":
    from encoding_utils import (
        get_info_from_video,
        get_list_rendition,
        launch_cmd,
        check_file
    )
else:
    from .encoding_utils import (
        get_info_from_video,
        get_list_rendition,
        launch_cmd,
        check_file
    )

# from unidecode import unidecode # third party package to remove accent
# import unicodedata

__author__ = "Nicolas CAN <nicolas.can@univ-lille.fr>"
__license__ = "LGPL v3"

image_codec = ["jpeg", "gif", "png", "bmp", "jpg"]

"""
 - Get video source
 - get alls track from video source
 - encode tracks in HLS and mp4
 - save it
"""
# https://trac.ffmpeg.org/wiki/Encode/H.264
FFMPEG_CMD = "ffmpeg"
FFMPEG_CRF = 20  # -crf 20 -maxrate 3M -bufsize 6M
FFMPEG_PRESET = "slow"
FFMPEG_PROFILE = "high"
FFMPEG_LEVEL = 3
FFMPEG_HLS_TIME = 2
# ffmpeg -hide_banner -i test5.mkv \
# -c:v libx264  -vf "scale=-2:360" -preset slow -profile:v high -pix_fmt yuv420p -level 3 -crf 20 -maxrate 1M -bufsize 2M -force_key_frames "expr:gte(t,n_forced*1)" -max_muxing_queue_size 4000 -c:a aac -ar 48000 -b:a 96k -movflags faststart  -y -vsync 0 360p.mp4 \
# -c:v libx264  -vf "scale=-2:720" -preset slow -profile:v high -pix_fmt yuv420p -level 3 -crf 20 -maxrate 3M -bufsize 6M -force_key_frames "expr:gte(t,n_forced*1)" -max_muxing_queue_size 4000 -c:a aac -ar 48000 -b:a 128k -movflags faststart  -y -vsync 0 720p.mp4 \
# -c:v libx264  -vf "scale=-2:1080" -preset slow -profile:v high -pix_fmt yuv420p -level 3 -crf 20 -maxrate 4M -bufsize 8M -force_key_frames "expr:gte(t,n_forced*1)" -max_muxing_queue_size 4000 -c:a aac -ar 48000 -b:a 192k -movflags faststart  -y -vsync 0 1080p.mp4


FFMPEG_INPUT = "-hide_banner -threads %(nb_threads)s -i %(input)s "
FFMPEG_LIBX = "libx264"
FFMPEG_MP4_ENCODE = (
    '-map 0:v:0 -map 0:a:0 -c:v %(libx)s  -vf "scale=-2:%(height)s" -preset %(preset)s -profile:v %(profile)s '
    + '-pix_fmt yuv420p -level %(level)s -crf %(crf)s -maxrate %(maxrate)s -bufsize %(bufsize)s '
    + '-sc_threshold 0 -force_key_frames "expr:gte(t,n_forced*1)" -max_muxing_queue_size 4000 '
    + '-c:a aac -ar 48000 -b:a %(ba)s -movflags faststart -y -vsync 0 "%(output)s" '
)
# https://gist.github.com/Andrey2G/78d42b5c87850f8fbadd0b670b0e6924
FFMPEG_HLS_ENCODE = (
    "-map 0:v:0 -map 0:a:0 -c:v %(libx)s  "  # take first index of video and audio
    + '-vf "scale=-2:%(height)s" -preset %(preset)s -profile:v %(profile)s '
    + '-pix_fmt yuv420p -level %(level)s -crf %(crf)s -maxrate %(maxrate)s -bufsize %(bufsize)s '
    + '-sc_threshold 0 -force_key_frames "expr:gte(t,n_forced*1)" -max_muxing_queue_size 4000 '
    + '-c:a aac -ar 48000 -b:a %(ba)s -hls_playlist_type vod -hls_time %(hls_time)s -hls_flags single_file '  # -hls_segment_type fmp4
    + '-master_pl_name "livestream.m3u8" -y -vsync 0 "%(output)s" '
)
FFMPEG_MP3_ENCODE = (
    '-vn -b:a %(audio_bitrate)s -vn -f mp3 "%(output)s" '
)
FFMPEG_M4A_ENCODE = (
    '-vn -c:a aac -b:a %(audio_bitrate)s "%(output)s" '
)
FFMPEG_NB_THREADS = 0
AUDIO_BITRATE = "192k"

EXTRACT_THUMBNAIL = '-map 0:%(index)s -an -c:v copy -y  "%(output)s" '
CREATE_THUMBNAIL = '-vframes 1 -an -ss %(time)s -y  "%(output)s" '
EXTRACT_SUBTITLE = '-map 0:%(index)s -f webvtt -y  "%(output)s" '


class Encoding_video:
    id = 0
    video_file = ""
    duration = 0
    list_video_track = {}
    list_audio_track = {}
    list_subtitle_track = {}
    list_image_track = {}
    list_mp4_files = {}
    list_hls_files = {}
    list_mp3_files = {}
    list_m4a_files = {}
    list_thumbnail_files = {}
    list_overview_files = {}
    list_subtitle_files = {}
    encoding_log = {}
    output_dir = ""
    start = 0
    stop = 0
    error_encoding = False

    def __init__(self, id=0, video_file=""):
        self.id = id
        self.video_file = video_file
        self.duration = 0
        self.list_video_track = {}
        self.list_audio_track = {}
        self.list_subtitle_track = {}
        self.list_image_track = {}
        self.list_mp4_files = {}
        self.list_hls_files = {}
        self.list_mp3_files = {}
        self.list_m4a_files = {}
        self.list_thumbnail_files = {}
        self.list_overview_files = {}
        self.encoding_log = {}
        self.output_dir = ""
        self.start = 0
        self.stop = 0
        self.error_encoding = False

    def is_video(self):
        return len(self.list_video_track) > 0

    def get_video_data(self):
        """
        get alls tracks from video source and put it in object passed in parameter
        """
        msg = "--> get_info_video" + "\n"
        probe_cmd = 'ffprobe -v quiet -show_format -show_streams \
                    -print_format json -i "{}"'.format(
            self.video_file
        )
        msg += probe_cmd + "\n"
        duration = 0
        info, return_msg = get_info_from_video(probe_cmd)
        msg += json.dumps(info, indent=2)
        msg += " \n"
        msg += return_msg + "\n"
        self.add_encoding_log("probe_cmd", probe_cmd, True, msg)
        try:
            duration = int(float("%s" % info["format"]["duration"]))
        except (RuntimeError, KeyError, AttributeError, ValueError, TypeError) as err:
            msg = "\nUnexpected error: {0}".format(err)
            self.add_encoding_log("duration", "", True, msg)
        self.duration = duration
        streams = info.get("streams", [])
        for stream in streams:
            self.add_stream(stream)

    def fix_duration(self, input_file):
        msg = "--> get_info_video" + "\n"
        probe_cmd = 'ffprobe -v quiet -show_entries format=duration -hide_banner  \
                    -of default=noprint_wrappers=1:nokey=1 -print_format json -i "{}"'.format(
            input_file
        )
        info = get_info_from_video(probe_cmd)
        duration = 0
        try:
            duration = int(float("%s" % info["format"]["duration"]))
        except (RuntimeError, KeyError, AttributeError, ValueError, TypeError) as err:
            msg += "\nUnexpected error: {0}".format(err)
            self.add_encoding_log("fix_duration", "", True, msg)
        self.duration = duration

    def add_stream(self, stream):
        codec_type = stream.get("codec_type", "unknown")
        # https://ffmpeg.org/doxygen/3.2/group__lavu__misc.html#ga9a84bba4713dfced21a1a56163be1f48
        if codec_type == "audio":
            codec = stream.get("codec_name", "unknown")
            self.list_audio_track["%s" % stream.get("index")] = {
                "sample_rate": stream.get("sample_rate", 0),
                "channels": stream.get("channels", 0),
            }
        if codec_type == "video":
            codec = stream.get("codec_name", "unknown")
            if any(ext in codec.lower() for ext in image_codec):
                self.list_image_track["%s" % stream.get("index")] = {
                    "width": stream.get("width", 0),
                    "height": stream.get("height", 0),
                }
            else:
                self.list_video_track["%s" % stream.get("index")] = {
                    "width": stream.get("width", 0),
                    "height": stream.get("height", 0),
                }
        if codec_type == "subtitle":
            codec = stream.get("codec_name", "unknown")
            language = ""
            if stream.get("tags"):
                language = stream.get("tags").get("language", "")
            self.list_subtitle_track["%s" % stream.get("index")] = {
                "language": language
            }

    def create_output_dir(self):
        dirname = os.path.dirname(self.video_file)
        output_dir = os.path.join(dirname, "%04d" % int(self.id))
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        self.output_dir = output_dir

    def get_mp4_command(self):
        mp4_command = "%s " % FFMPEG_CMD
        list_rendition = get_list_rendition()
        first_item = list_rendition.popitem(last=False)
        mp4_command += FFMPEG_INPUT % {
            "input": self.video_file,
            "nb_threads": FFMPEG_NB_THREADS
        }
        output_file = os.path.join(self.output_dir, "%sp.mp4" % first_item[0])
        mp4_command += FFMPEG_MP4_ENCODE % {
            "libx": FFMPEG_LIBX,
            "height": first_item[0],
            "preset": FFMPEG_PRESET,
            "profile": FFMPEG_PROFILE,
            "level": FFMPEG_LEVEL,
            "crf": FFMPEG_CRF,
            "maxrate": first_item[1]["maxrate"],
            "bufsize": first_item[1]["maxrate"],
            "ba": first_item[1]["audio_bitrate"],
            "output": output_file
        }
        self.list_mp4_files[first_item[0]] = output_file
        """
        il est possible de faire ainsi :
        mp4_command += FFMPEG_MP4_ENCODE.format(
            height=first_item[0],
            [...]
        )
        """
        in_height = list(self.list_video_track.items())[0][1]["height"]
        for rend in list_rendition:
            if in_height >= rend:
                output_file = os.path.join(self.output_dir, "%sp.mp4" % rend)
                mp4_command += FFMPEG_MP4_ENCODE % {
                    "libx": FFMPEG_LIBX,
                    "height": rend,
                    "preset": FFMPEG_PRESET,
                    "profile": FFMPEG_PROFILE,
                    "level": FFMPEG_LEVEL,
                    "crf": FFMPEG_CRF,
                    "maxrate": list_rendition[rend]["maxrate"],
                    "bufsize": list_rendition[rend]["maxrate"],
                    "ba": list_rendition[rend]["audio_bitrate"],
                    "output": output_file
                }
                self.list_mp4_files[first_item[0]] = output_file
        return mp4_command

    def get_hls_command(self):
        hls_command = "%s " % FFMPEG_CMD
        list_rendition = get_list_rendition()
        first_item = list_rendition.popitem(last=False)
        hls_command += FFMPEG_INPUT % {
            "input": self.video_file,
            "nb_threads": FFMPEG_NB_THREADS
        }
        output_file = os.path.join(self.output_dir, "%sp.m3u8" % first_item[0])
        hls_command += FFMPEG_HLS_ENCODE % {
            "libx": FFMPEG_LIBX,
            "height": first_item[0],
            "preset": FFMPEG_PRESET,
            "profile": FFMPEG_PROFILE,
            "level": FFMPEG_LEVEL,
            "crf": FFMPEG_CRF,
            "maxrate": first_item[1]["maxrate"],
            "bufsize": first_item[1]["maxrate"],
            "ba": first_item[1]["audio_bitrate"],
            "hls_time": FFMPEG_HLS_TIME,
            "output": output_file
        }
        self.list_hls_files[first_item[0]] = output_file
        in_height = list(self.list_video_track.items())[0][1]["height"]
        for rend in list_rendition:
            if in_height >= rend:
                output_file = os.path.join(self.output_dir, "%sp.m3u8" % rend)
                hls_command += FFMPEG_HLS_ENCODE % {
                    "libx": FFMPEG_LIBX,
                    "height": rend,
                    "preset": FFMPEG_PRESET,
                    "profile": FFMPEG_PROFILE,
                    "level": FFMPEG_LEVEL,
                    "crf": FFMPEG_CRF,
                    "maxrate": list_rendition[rend]["maxrate"],
                    "bufsize": list_rendition[rend]["maxrate"],
                    "ba": list_rendition[rend]["audio_bitrate"],
                    "hls_time": FFMPEG_HLS_TIME,
                    "output": output_file
                }
                self.list_hls_files[first_item[0]] = output_file
        return hls_command

    def encode_video_part(self):
        mp4_command = self.get_mp4_command()
        return_value, return_msg = launch_cmd(mp4_command)
        self.add_encoding_log("mp4_command", mp4_command, return_value, return_msg)
        if not return_value:
            self.error_encoding = True
        if self.duration == 0:
            list_rendition = get_list_rendition()
            first_item = list_rendition.popitem(last=False)
            self.fix_duration(self.list_mp4_files[first_item[0]])
        hls_command = self.get_hls_command()
        return_value, return_msg = launch_cmd(hls_command)
        self.add_encoding_log("hls_command", hls_command, return_value, return_msg)

    def get_mp3_command(self):
        mp3_command = "%s " % FFMPEG_CMD
        mp3_command += FFMPEG_INPUT % {
            "input": self.video_file,
            "nb_threads": FFMPEG_NB_THREADS
        }
        output_file = os.path.join(self.output_dir, "audio_%s.mp3" % AUDIO_BITRATE)
        mp3_command += FFMPEG_MP3_ENCODE % {
            "audio_bitrate": AUDIO_BITRATE,
            "output": output_file,
        }
        self.list_mp3_files[AUDIO_BITRATE] = output_file
        return mp3_command

    def get_m4a_command(self):
        m4a_command = "%s " % FFMPEG_CMD
        m4a_command += FFMPEG_INPUT % {
            "input": self.video_file,
            "nb_threads": FFMPEG_NB_THREADS
        }
        output_file = os.path.join(self.output_dir, "audio_%s.m4a" % AUDIO_BITRATE)
        m4a_command += FFMPEG_M4A_ENCODE % {
            "audio_bitrate": AUDIO_BITRATE,
            "output": output_file,
        }
        self.list_m4a_files[AUDIO_BITRATE] = output_file
        return m4a_command

    def encode_audio_part(self):
        mp3_command = self.get_mp3_command()
        return_value, return_msg = launch_cmd(mp3_command)
        self.add_encoding_log("mp3_command", mp3_command, return_value, return_msg)
        if self.duration == 0:
            new_k = list(self.list_mp3_files)[0]
            self.fix_duration(self.list_mp3_files[new_k])
        if not self.is_video():
            m4a_command = self.get_m4a_command()
            return_value, return_msg = launch_cmd(m4a_command)
            self.add_encoding_log("m4a_command", m4a_command, return_value, return_msg)

    def get_extract_thumbnail_command(self):
        thumbnail_command = "%s " % FFMPEG_CMD
        thumbnail_command += FFMPEG_INPUT % {
            "input": self.video_file,
            "nb_threads": FFMPEG_NB_THREADS
        }
        for img in self.list_image_track:
            output_file = os.path.join(self.output_dir, "thumbnail_%s.png" % img)
            thumbnail_command += EXTRACT_THUMBNAIL % {
                "index": img,
                "output": output_file
            }
            self.list_thumbnail_files[img] = output_file
        return thumbnail_command

    def get_create_thumbnail_command(self):
        thumbnail_command = "%s " % FFMPEG_CMD
        list_rendition = get_list_rendition()
        first_item = list_rendition.popitem(last=False)
        input_file = self.list_mp4_files[first_item[0]]
        thumbnail_command += FFMPEG_INPUT % {
            "input": input_file,
            "nb_threads": FFMPEG_NB_THREADS
        }
        if self.duration < 10 :
            output_file = os.path.join(self.output_dir, "thumbnail_1.png")
            thumbnail_command += CREATE_THUMBNAIL % {
                "time": int(self.duration / 2),
                "output": output_file
            }
            self.list_thumbnail_files["1"] = output_file
        elif 10 <= self.duration < 60:
            output_file = os.path.join(self.output_dir, "thumbnail_1.png")
            thumbnail_command += CREATE_THUMBNAIL % {
                "time": int(self.duration / 3),
                "output": output_file
            }
            self.list_thumbnail_files["1"] = output_file
            output_file = os.path.join(self.output_dir, "thumbnail_2.png")
            thumbnail_command += CREATE_THUMBNAIL % {
                "time": int((self.duration / 3) * 2),
                "output": output_file
            }
            self.list_thumbnail_files["2"] = output_file
        else:
            for dur in range(1, 4):
                output_file = os.path.join(self.output_dir, "thumbnail_%s.png" % dur)
                thumbnail_command += CREATE_THUMBNAIL % {
                    "time": int((self.duration / 4) * dur),
                    "output": output_file
                }
                self.list_thumbnail_files["%s" % dur] = output_file
        return thumbnail_command

    def create_overview(self):
        list_rendition = get_list_rendition()
        first_item = list_rendition.popitem(last=False)
        image_width = int(int(first_item[1]["resolution"].split("x")[0]) / 4)  # width of generate image file
        image_height = int(int(first_item[1]["resolution"].split("x")[1]) / 4)  # width of generate image file
        input_file = self.list_mp4_files[first_item[0]]
        nb_img = 100
        step = 1
        if self.duration < 100:
            # nb_img = int(self.duration * 10 / 100)
            step = 10  # on ne fait que 10 images si la video dure moins de 100 sec.
        overviewimagefilename = os.path.join(self.output_dir, "overview.png")
        image_url = os.path.basename(overviewimagefilename)
        overviewfilename = os.path.join(self.output_dir, "overview.vtt")
        webvtt = WebVTT()
        for i in range(1, nb_img, step):
            output_file = os.path.join(self.output_dir, "thumbnail_%s.png" % i)
            cmd_ffmpegthumbnailer = (
                'ffmpegthumbnailer -t "%(stamp)s" '
                + '-s "%(image_width)s" -i %(source)s -c png '
                + '-o %(output_file)s ') % {
                    "stamp": str(i) + "%",
                    "source": input_file,
                    "output_file": output_file,
                    "image_width": image_width
            }
            return_value, return_msg = launch_cmd(cmd_ffmpegthumbnailer)
            # self.add_encoding_log("ffmpegthumbnailer_%s" % i, cmd_ffmpegthumbnailer, return_value, return_msg)
            if return_value and check_file(output_file):
                cmd_montage = (
                    "montage -geometry +0+0 %(overviewimagefilename)s \
                    %(output_file)s  %(overviewimagefilename)s"
                    % {"overviewimagefilename": overviewimagefilename, "output_file": output_file}
                )
                return_value, return_msg = launch_cmd(cmd_montage)
                # self.add_encoding_log("cmd_montage_%s" % i, cmd_montage, return_value, return_msg)
                os.remove(output_file)
                start = format(float(self.duration * i / 100), ".3f")
                end = format(float(self.duration * (i + 1) / 100), ".3f")
                start_time = time.strftime("%H:%M:%S", time.gmtime(int(str(start).split(".")[0])))
                start_time += ".%s" % (str(start).split(".")[1])
                end_time = time.strftime(
                    "%H:%M:%S", time.gmtime(int(str(end).split(".")[0]))
                ) + ".%s" % (str(end).split(".")[1])
                caption = Caption(
                    "%s" % start_time,
                    "%s" % end_time,
                    "%s#xywh=%d,%d,%d,%d"
                    % (image_url, image_width * i, 0, image_width, image_height),
                )
                webvtt.captions.append(caption)
        webvtt.save(overviewfilename)
        if check_file(overviewfilename) and check_file(overviewimagefilename):
            self.list_overview_files["0"] = overviewimagefilename
            self.list_overview_files["1"] = overviewfilename
            # self.encoding_log += "\n- overviewfilename:\n%s" % overviewfilename
        else:
            self.add_encoding_log("create_overview", "", False, "")

    def encode_image_part(self):
        if len(self.list_image_track) > 0:
            thumbnail_command = self.get_extract_thumbnail_command()
            return_value, return_msg = launch_cmd(thumbnail_command)
            self.add_encoding_log("extract_thumbnail_command", thumbnail_command, return_value, return_msg)
        elif self.is_video():
            thumbnail_command = self.get_create_thumbnail_command()
            return_value, return_msg = launch_cmd(thumbnail_command)
            self.add_encoding_log("create_thumbnail_command", thumbnail_command, return_value, return_msg)
            # on ne fait pas d'overview pour les videos de moins de 10 secondes
            if self.duration > 10 :
                self.create_overview()

    def get_extract_subtitle_command(self):
        subtitle_command = "%s " % FFMPEG_CMD
        subtitle_command += FFMPEG_INPUT % {
            "input": self.video_file,
            "nb_threads": FFMPEG_NB_THREADS
        }
        for img in self.list_subtitle_track:
            lang = self.list_subtitle_track[img]
            output_file = os.path.join(self.output_dir, "subtitle_%s.vtt" % lang)
            subtitle_command += EXTRACT_SUBTITLE % {
                "index": img,
                "output": output_file
            }
            self.list_subtitle_files[img] = [lang, output_file]
        return subtitle_command

    def get_subtitle_part(self):
        if len(self.list_subtitle_track) > 0:
            subtitle_command = self.get_extract_subtitle_command()
            return_value, return_msg = launch_cmd(subtitle_command)
            self.add_encoding_log("subtitle_command", subtitle_command, return_value, return_msg)

    def export_to_json(self):
        data_to_dump = {}
        for attribute, value in self.__dict__.items():
            data_to_dump[attribute] = value
        with open(self.output_dir + "/info_video.json", "w") as outfile:
            json.dump(data_to_dump, outfile, indent=2)

    def add_encoding_log(self, title, command, result, msg):
        self.encoding_log[title] = {
            "command": command,
            "result": result,
            "msg": msg
        }
        if result is False and self.error_encoding is False:
            self.error_encoding = True

    def start_encode(self):
        self.create_output_dir()
        self.get_video_data()
        print(
            self.id, self.video_file, self.duration
        )
        if self.is_video():
            self.encode_video_part()
        if len(self.list_audio_track) > 0:
            self.encode_audio_part()
        self.encode_image_part()
        if len(self.list_subtitle_track) > 0:
            self.get_subtitle_part()
        self.export_to_json()


def fix_input(input):
    filename = ""
    if args.input.startswith('/'):
        path_file = args.input
    else:
        path_file = os.path.join(os.getcwd(), args.input)
    print(path_file)
    if os.access(path_file, os.F_OK) and os.stat(path_file).st_size > 0:
        # remove accent and space
        filename = "".join(
            (
                c
                for c in unicodedata.normalize("NFD", path_file)
                if unicodedata.category(c) != "Mn"
            )
        )
        filename = filename.replace(" ", "_")
        os.rename(
            path_file,
            filename,
        )
        print("Encoding file {} \n".format(filename))
    return filename

