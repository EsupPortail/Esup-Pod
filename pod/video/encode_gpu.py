#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Encode.py
# Encoding video for Pod
#
# Nicolas CAN <nicolas.can@univ-lille.fr>
# Wed Sep  2 11:49:12 CEST 2020

from __future__ import absolute_import, division, print_function
import os
import argparse
import subprocess
import shlex
import json
import time

from json.decoder import JSONDecodeError

from timeit import default_timer as timer
# from unidecode import unidecode # third partu package to remove accent
import unicodedata

DEBUG = False

VIDEOS_DIR = "videos"
VIDEOS_OUTPUT_DIR = "encoding_videos"
HWACCEL_DEVICE = 0

image_codec = ["jpeg", "gif", "png", "bmp", "jpg"]

LIST_CODEC = ("h264",
              "hevc",
              "mjpeg",
              "mpeg1",
              "mpeg2",
              "mpeg4",
              "vc1",
              "vp8",
              "vp9")
# https://trac.ffmpeg.org/wiki/Encode/MP3
MP3 = 'time ffmpeg -i {input} -hide_banner -y -c:a libmp3lame -q:a 2 \
    -sample_rate 44100 -vn -threads 0 "{output_dir}/audio_192k_{output}.mp3"'

M4A = 'time ffmpeg -i {input} -hide_banner -y -c:a aac -sample_rate 44100 \
    -q:a 2 -vn -threads 0 "{output_dir}/audio_192k_{output}.m4a"'

EXTRACT_THUMBNAIL = 'time ffmpeg -i {input} -hide_banner \
    -y {output_dir}/thumbnail.jpg'

CPU = 'time ffmpeg -hide_banner -y -i {input} '
GPU = 'time ffmpeg -y -vsync 0 -hwaccel_device {hwaccel_device} \
    -hwaccel cuvid -c:v {codec}_cuvid -i {input} '

SUBTIME = ' '

COMMON = ' -c:a aac -ar 48000 '\
    '-strict experimental -profile:v high -pixel_format yuv420p '\
    '-force_key_frames "expr:gte(t,n_forced*1)" '\
    '-preset slow -qmin 20 -qmax 50 '\

scale_mixed = \
    '-vf "fade,hwupload_cuda,scale_npp=-2:{height}:interp_algo=super" \
    -c:v h264_nvenc '
scale_gpu = '-vf "scale_npp=-2:{height}:interp_algo=super" -c:v h264_nvenc '
scale_cpu = '-vf "scale=-2:{height}" -c:v h264 '

rate_360 = '-b:a 96k -minrate 500k -b:v 750k -maxrate 1000k -bufsize 1500k '
rate_720 = '-b:a 128k -minrate 1000k -b:v 2000k -maxrate 3000k -bufsize 4000k '
rate_1080 = '-b:a 192k -minrate 2M -b:v 3M -maxrate 4500k -bufsize 6M '

end_360_m3u8 = rate_360 +\
    '-hls_playlist_type vod -hls_time 2 \
    -hls_flags single_file {output_dir}/360p_{output}.m3u8 '

end_360_mp4 = rate_360 +\
    '-movflags faststart -write_tmcd 0 \
    "{output_dir}/360p_{output}.mp4" '

end_720_m3u8 = rate_720 +\
    '-hls_playlist_type vod -hls_time 2 \
    -hls_flags single_file {output_dir}/720p_{output}.m3u8 '

end_720_mp4 = rate_720 +\
    '-movflags faststart -write_tmcd 0 "{output_dir}/720p_{output}.mp4" '

end_1080_m3u8 = rate_720 +\
    '-hls_playlist_type vod -hls_time 2 \
    -hls_flags single_file {output_dir}/1080p_{output}.m3u8 '

# :force_original_aspect_ratio=decrease,pad=1280:720:-1:-1:color=black

# get duration
# encode playlist
# encode MP4
# create overview
# create and save thumbnails


def encode_with_gpu(format, codec, height, file):
    msg = "--> encode_with_gpu \n"
    return_value = False
    if encode("gpu", format, codec, height, file):
        msg += "Encode GPU %s ok \n" % format
        return_value = True
    else:
        if encode("mixed", format, codec, height, file):
            msg += "Encode Mixed %s ok \n" % format
            return_value = True
        else:
            if encode("cpu", format, codec, height, file):
                msg += "Encode CPU %s ok \n" % format
                return_value = True
    if return_value is False:
        msg += 20*"////" + "\n"
        msg += 'ERROR ENCODING %s FOR FILE %s \n' % (format, file)
    encode_log(msg)
    return return_value


def encode_without_gpu(format, codec, height, file):
    msg = "--> encode_with_gpu \n"
    return_value = False
    if encode("mixed", format, codec, height, file):
        msg += "Encode MIXED %s ok \n" % format
        return_value = True
    else:
        if encode("cpu", format, codec, height, file):
            msg += "Encode CPU %s ok \n" % format
            return_value = True
    if return_value is False:
        msg += 20*"////" + "\n"
        msg += 'ERROR ENCODING %s FOR FILE %s \n' % (format, file)
    return return_value


def get_cmd_gpu(format, codec, height, file):
    ffmpeg_cmd = ""
    ffmpeg_cmd = GPU.format(
        hwaccel_device=HWACCEL_DEVICE, codec=codec,
        input=os.path.join(VIDEOS_DIR, file))
    ffmpeg_cmd = ffmpeg_cmd
    ffmpeg_cmd = ffmpeg_cmd + COMMON + scale_gpu.format(height=360)
    filename = os.path.splitext(os.path.basename(file))[0]
    filename = ''.join(
        (
            c for c in unicodedata.normalize(
                'NFD', filename
            ) if unicodedata.category(c) != 'Mn'
        )
    )
    if format == "m3u8":
        ffmpeg_cmd = ffmpeg_cmd + SUBTIME +\
            end_360_m3u8.format(
                output_dir=VIDEOS_OUTPUT_DIR,
                output=filename
            )
        add_info_video(
            "encode_video",
            {
                "encoding_format": "video/mp2t",
                "rendition": "640x360",
                "filename": "360p_{output}.m3u8".format(output=filename),
            },
            True
        )
    else:
        ffmpeg_cmd = ffmpeg_cmd + SUBTIME +\
            end_360_mp4.format(
                output_dir=VIDEOS_OUTPUT_DIR,
                output=filename
            )
        add_info_video(
            "encode_video",
            {
                "encoding_format": "video/mp4",
                "rendition": "640x360",
                "filename": "360p_{output}.mp4".format(output=filename),
            },
            True
        )
    if height >= 720:
        ffmpeg_cmd = ffmpeg_cmd + COMMON + scale_gpu.format(height=720)
        if format == "m3u8":
            ffmpeg_cmd = ffmpeg_cmd + SUBTIME +\
                end_720_m3u8.format(
                    output_dir=VIDEOS_OUTPUT_DIR,
                    output=filename
                )
            add_info_video(
                "encode_video",
                {
                    "encoding_format": "video/mp2t",
                    "rendition": "1280x720",
                    "filename": "720p_{output}.m3u8".format(output=filename),
                },
                True
            )
        else:
            ffmpeg_cmd = ffmpeg_cmd + SUBTIME +\
                end_720_mp4.format(
                    output_dir=VIDEOS_OUTPUT_DIR,
                    output=filename)
            add_info_video(
                "encode_video",
                {
                    "encoding_format": "video/mp4",
                    "rendition": "1280x720",
                    "filename": "720p_{output}.mp4".format(output=filename),
                },
                True
            )
    if height >= 1080:
        ffmpeg_cmd = ffmpeg_cmd + COMMON + scale_gpu.format(height=1080)
        if format == "m3u8":
            ffmpeg_cmd = ffmpeg_cmd + SUBTIME +\
                end_1080_m3u8.format(
                    output_dir=VIDEOS_OUTPUT_DIR,
                    output=filename)
            add_info_video(
                "encode_video",
                {
                    "encoding_format": "video/mp2t",
                    "rendition": "1920x1080",
                    "filename": "1080p_{output}.m3u8".format(output=filename),
                },
                True
            )
    return ffmpeg_cmd


def get_cmd_mixed(format, codec, height, file):
    ffmpeg_cmd = ""
    ffmpeg_cmd = CPU.format(
        codec=codec, input=os.path.join(VIDEOS_DIR, file))
    ffmpeg_cmd = ffmpeg_cmd + COMMON
    ffmpeg_cmd = ffmpeg_cmd + scale_mixed.format(height=360)
    filename = os.path.splitext(os.path.basename(file))[0]
    filename = ''.join(
        (
            c for c in unicodedata.normalize(
                'NFD', filename
            ) if unicodedata.category(c) != 'Mn'
        )
    )
    if format == "m3u8":
        ffmpeg_cmd = ffmpeg_cmd + SUBTIME +\
            end_360_m3u8.format(
                output_dir=VIDEOS_OUTPUT_DIR,
                output=filename
            )
        add_info_video(
            "encode_video",
            {
                "encoding_format": "video/mp2t",
                "rendition": "640x360",
                "filename": "360p_{output}.m3u8".format(output=filename),
            },
            True
        )
    else:
        ffmpeg_cmd = ffmpeg_cmd + SUBTIME +\
            end_360_mp4.format(
                output_dir=VIDEOS_OUTPUT_DIR,
                output=filename
            )
        add_info_video(
            "encode_video",
            {
                "encoding_format": "video/mp4",
                "rendition": "640x360",
                "filename": "360p_{output}.mp4".format(output=filename),
            },
            True
        )
    if height >= 720:
        ffmpeg_cmd = ffmpeg_cmd + scale_mixed.format(height=720)
        if format == "m3u8":
            ffmpeg_cmd = ffmpeg_cmd + SUBTIME +\
                end_720_m3u8.format(
                    output_dir=VIDEOS_OUTPUT_DIR,
                    output=filename)
            add_info_video(
                "encode_video",
                {
                    "encoding_format": "video/mp2t",
                    "rendition": "1280x720",
                    "filename": "720p_{output}.m3u8".format(output=filename),
                },
                True
            )
        else:
            ffmpeg_cmd = ffmpeg_cmd + SUBTIME +\
                end_720_mp4.format(
                    output_dir=VIDEOS_OUTPUT_DIR,
                    output=filename)
            add_info_video(
                "encode_video",
                {
                    "encoding_format": "video/mp4",
                    "rendition": "1280x720",
                    "filename": "720p_{output}.mp4".format(output=filename),
                },
                True
            )
    if height >= 1080:
        ffmpeg_cmd = ffmpeg_cmd + scale_mixed.format(height=1080)
        if format == "m3u8":
            ffmpeg_cmd = ffmpeg_cmd + SUBTIME +\
                end_1080_m3u8.format(
                    output_dir=VIDEOS_OUTPUT_DIR,
                    output=filename)
            add_info_video(
                "encode_video",
                {
                    "encoding_format": "video/mp2t",
                    "rendition": "1920x1080",
                    "filename": "1080p_{output}.m3u8".format(output=filename),
                },
                True
            )
    return ffmpeg_cmd


def get_cmd_cpu(format, codec, height, file):
    ffmpeg_cmd = ""
    ffmpeg_cmd = CPU.format(
        codec=codec, input=os.path.join(VIDEOS_DIR, file))
    ffmpeg_cmd = ffmpeg_cmd + COMMON
    ffmpeg_cmd = ffmpeg_cmd + scale_cpu.format(height=360)
    filename = os.path.splitext(os.path.basename(file))[0]
    filename = ''.join(
        (
            c for c in unicodedata.normalize(
                'NFD', filename
            ) if unicodedata.category(c) != 'Mn'
        )
    )
    if format == "m3u8":
        ffmpeg_cmd = ffmpeg_cmd + SUBTIME +\
            end_360_m3u8.format(
                output_dir=VIDEOS_OUTPUT_DIR,
                output=filename
            )
        add_info_video(
            "encode_video",
            {
                "encoding_format": "video/mp2t",
                "rendition": "640x360",
                "filename": "360p_{output}.m3u8".format(output=filename),
            },
            True
        )
    else:
        ffmpeg_cmd = ffmpeg_cmd + SUBTIME +\
            end_360_mp4.format(
                output_dir=VIDEOS_OUTPUT_DIR,
                output=filename
            )
        add_info_video(
            "encode_video",
            {
                "encoding_format": "video/mp4",
                "rendition": "640x360",
                "filename": "360p_{output}.mp4".format(output=filename),
            },
            True
        )
    if height >= 720:
        ffmpeg_cmd = ffmpeg_cmd + scale_cpu.format(height=720)
        if format == "m3u8":
            ffmpeg_cmd = ffmpeg_cmd + SUBTIME +\
                end_720_m3u8.format(
                    output_dir=VIDEOS_OUTPUT_DIR,
                    output=filename
                )
            add_info_video(
                "encode_video",
                {
                    "encoding_format": "video/mp2t",
                    "rendition": "1280x720",
                    "filename": "720p_{output}.m3u8".format(output=filename),
                },
                True
            )
        else:
            ffmpeg_cmd = ffmpeg_cmd + SUBTIME +\
                end_720_mp4.format(
                    output_dir=VIDEOS_OUTPUT_DIR,
                    output=filename
                )
            add_info_video(
                "encode_video",
                {
                    "encoding_format": "video/mp4",
                    "rendition": "1280x720",
                    "filename": "720p_{output}.mp4".format(output=filename),
                },
                True
            )
    if height >= 1080:
        ffmpeg_cmd = ffmpeg_cmd + scale_cpu.format(height=1080)
        if format == "m3u8":
            ffmpeg_cmd = ffmpeg_cmd + SUBTIME +\
                end_1080_m3u8.format(
                    output_dir=VIDEOS_OUTPUT_DIR,
                    output=filename
                )
            add_info_video(
                "encode_video",
                {
                    "encoding_format": "video/mp2t",
                    "rendition": "1920x1080",
                    "filename": "1080p_{output}.m3u8".format(output=filename),
                },
                True
            )
    return ffmpeg_cmd


def launch_cmd(ffmpeg_cmd, type, format):
    msg = ""
    encode_start = timer()
    return_value = False
    try:
        output = subprocess.run(shlex.split(
            ffmpeg_cmd), stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        encode_end = timer() - encode_start
        msg += ffmpeg_cmd + "\n"
        msg += 'Encode file in {:.3}s.\n'.format(encode_end)
        # msg += "\n".join(output.stdout.decode().split('\n'))
        msg += output.stdout.decode()
        msg += "\n"
        if output.returncode != 0:
            msg += "ERROR RETURN CODE for type=%s and format=%s : %s" % (
                type, format, output.returncode)
        else:
            return_value = True
    except subprocess.CalledProcessError as e:
        # raise RuntimeError('ffmpeg returned non-zero status: {}'.format(
        # e.stderr))
        msg += 20*"////" + "\n"
        msg += "Runtime Error: {0}\n".format(e)

    except OSError as err:
        # raise OSError(e.errno, 'ffmpeg not found: {}'.format(e.strerror))
        msg += 20*"////" + "\n"
        msg += "OS error: {0}\n".format(err)
    return return_value, msg


def encode(type, format, codec, height, file):
    msg = "--> encode" + "\n"

    ffmpeg_cmd = ""
    filename = os.path.splitext(os.path.basename(file))[0]
    filename = ''.join(
        (
            c for c in unicodedata.normalize(
                'NFD', filename
            ) if unicodedata.category(c) != 'Mn'
        )
    )

    if type == "gpu":
        ffmpeg_cmd = get_cmd_gpu(format, codec, height, file)

    if type == "mixed":
        ffmpeg_cmd = get_cmd_mixed(format, codec, height, file)

    if type == "cpu":
        ffmpeg_cmd = get_cmd_cpu(format, codec, height, file)

    if type == "mp3":
        ffmpeg_cmd = MP3.format(
            input=os.path.join(VIDEOS_DIR, file),
            output_dir=VIDEOS_OUTPUT_DIR,
            output=filename)
        add_info_video(
            "encode_audio",
            {
                "encoding_format": "audio/mp3",
                "filename": "audio_192k_{output}.mp3".format(output=filename),
            },
            True
        )
    if type == "m4a":
        ffmpeg_cmd = M4A.format(
            input=os.path.join(VIDEOS_DIR, file),
            output_dir=VIDEOS_OUTPUT_DIR,
            output=filename)
        add_info_video(
            "encode_audio",
            {
                "encoding_format": "video/mp4",
                "filename": "audio_192k_{output}.m4a".format(output=filename),
            },
            True
        )
    if type == "thumbnail":
        ffmpeg_cmd = EXTRACT_THUMBNAIL.format(
            output_dir=VIDEOS_OUTPUT_DIR, input=os.path.join(VIDEOS_DIR, file))
        add_info_video(
            "encode_thumbnail",
            {
                "filename": "thumbnail.jpg",
            },
            False
        )

    return_value, return_msg = launch_cmd(ffmpeg_cmd, type, format)

    encode_log(msg+return_msg)
    return return_value


def get_info_from_video(probe_cmd):
    info = None
    msg = ""
    try:
        output = subprocess.check_output(
            shlex.split(probe_cmd), stderr=subprocess.PIPE)
        info = json.loads(output)
    except subprocess.CalledProcessError as e:
        # raise RuntimeError('ffprobe returned non-zero status: {}'.format(
        # e.stderr))
        msg += 20*"////" + "\n"
        msg += "Runtime Error: {0}\n".format(e)
    except OSError as err:
        # raise OSError(e.errno, 'ffprobe not found: {}'.format(e.strerror))
        msg += 20*"////" + "\n"
        msg += "OS error: {0}\n".format(err)
    return info, msg


def get_info_video(file):
    msg = "--> get_info_video" + "\n"
    probe_cmd = 'ffprobe -v quiet -show_format -show_streams \
                -print_format json -i {}/{}'.format(VIDEOS_DIR, file)
    if DEBUG:
        print(probe_cmd)
    msg += probe_cmd + "\n"
    has_stream_video = False
    has_stream_thumbnail = False
    has_stream_audio = False
    codec = ""
    height = 0
    duration = 0
    info, return_msg = get_info_from_video(probe_cmd)
    msg += json.dumps(info, indent=2)
    msg += " \n"
    msg += return_msg + "\n"
    duration = int(float("%s" % info["format"]['duration']))
    streams = info.get("streams", [])
    for stream in streams:
        msg += stream.get("codec_type", "unknown")
        msg += ": "
        msg += stream.get("codec_name", "unknown")
        if stream.get("codec_type", "unknown") == "video":
            codec = stream.get("codec_name", "unknown")
            has_stream_thumbnail = any(ext in codec.lower()
                                       for ext in image_codec)
            if not has_stream_thumbnail:
                has_stream_video = True
                height = stream.get("height", 0)
        if stream.get("codec_type", "unknown") == "audio":
            has_stream_audio = True

    encode_log(msg)

    return {
        "has_stream_video": has_stream_video,
        "has_stream_thumbnail": has_stream_thumbnail,
        "has_stream_audio": has_stream_audio,
        "codec": codec,
        "height": height,
        "duration": duration
    }


def launch_encode_video(info_video, file):
    encode_m3u8 = encode_mp4 = True
    codec = info_video.get("codec", "")
    height = info_video.get("height", 0)
    if codec in LIST_CODEC:
        encode_m3u8 = encode_with_gpu("m3u8", codec, height, file)
        encode_mp4 = encode_with_gpu("mp4", codec, height, file)
    else:
        encode_m3u8 = encode_without_gpu("m3u8", codec, height, file)
        encode_mp4 = encode_without_gpu("mp4", codec, height, file)
    return encode_m3u8, encode_mp4


def launch_encode_audio(info_video, file):
    encode_audio = True
    msg = ""
    if not info_video.get("has_stream_video", False):
        if encode("m4a", "", "", 0, file):
            msg += "encode m4a ok" + "\n"
        else:
            encode_audio = False
            msg += 20*"////" + "\n"
            msg += "error m4a"
    if encode("mp3", "", "", 0, file):
        msg += "encode mp3 ok" + "\n"
    else:
        encode_audio = False
        msg += 20*"////" + "\n"
        msg += "error mp3" + "\n"
    return encode_audio, msg


def launch_encode(info_video, file):
    msg = "--> launch_encode" + "\n"
    encode_m3u8 = encode_mp4 = True
    if info_video.get("has_stream_video", False):
        encode_m3u8, encode_mp4 = launch_encode_video(info_video, file)
    encode_thumbnail = True
    if info_video.get("has_stream_thumbnail", False):
        if encode("thumbnail", "jpg", "", 0, file):
            msg += "thumbnail ok" + "\n"
        else:
            encode_thumbnail = False
            msg += 20*"////" + "\n"
            msg += "error thumbnail" + "\n"
    encode_audio = True
    if info_video.get("has_stream_audio", False):
        encode_audio, return_msg = launch_encode_audio(info_video, file)
        msg += return_msg
    encode_log(msg)
    return encode_audio and encode_thumbnail and encode_m3u8 and encode_mp4


def encode_log(msg):
    if DEBUG:
        print(msg)
    with open(VIDEOS_OUTPUT_DIR + "/encoding.log", "a") as f:
        f.write('\n')
        f.write(msg)
        f.write('\n')


def add_info_video(key, value, append=False):
    data = {}
    try:
        with open(VIDEOS_OUTPUT_DIR + "/info_video.json") as json_file:
            data = json.load(json_file)
    except FileNotFoundError:
        pass
    except JSONDecodeError:
        pass
    if DEBUG:
        print(data, data.get(key), key, value, append)
    if data.get(key) and append:
        val = data[key]
        print(type(val), type(data[key]))
        data[key] = val.append(value) if (type(val) is list) else [val, value]
    else:
        data[key] = [value] if append else value
    with open(VIDEOS_OUTPUT_DIR + "/info_video.json", "w") as outfile:
        json.dump(data, outfile, indent=2)


if __name__ == "__main__":

    msg = "--> Main \n"
    msg += "- lancement cycle encodage : %s \n" % time.ctime()
    # python3 encode.py
    # --device {CUDA_VISIBLE_DEVICES}
    # --dir {BASE_DIR}/encoding/{JOB_NAME}
    # --input {INPUT_FILE}
    # --job ${SLURM_JOB_ID}
    # --name {JOB_NAME}
    parser = argparse.ArgumentParser(description='Running encoding video.')
    parser.add_argument('--device', required=True,
                        help='CUDA_VISIBLE_DEVICES')
    parser.add_argument('--dir', required=False,
                        help='base dir to encode')
    parser.add_argument('--input', required=True,
                        help='name of input file to encode')
    parser.add_argument('--job', required=False,
                        help='the ID of job')
    parser.add_argument('--name', required=False,
                        help='the name of job')
    parser.add_argument('--debug', required=False,
                        help='run job in debug mode')
    args = parser.parse_args()
    msg += 'Using device {} \n'.format(args.device)
    msg += 'Using job {} \n'.format(args.job)
    msg += 'Using name {} \n'.format(args.name)

    # --dir /workdir/nicolas.can//encoding/encoding-12689
    # --input videos/fa131629[...]b9a2424/clip-pod.mp4

    DEBUG = True if args.debug and args.debug == "True" else False

    SUBTIME = '-ss 00:00:00 -to 00:01:00 ' if DEBUG else ' '

    VIDEOS_DIR = args.dir if args.dir else "videos"

    VIDEOS_OUTPUT_DIR = os.path.join(
        VIDEOS_DIR, os.path.basename(VIDEOS_DIR).split('-')[-1]) if args.dir \
        else os.path.join(VIDEOS_DIR, VIDEOS_OUTPUT_DIR)
    if not os.path.exists(VIDEOS_OUTPUT_DIR):
        os.makedirs(VIDEOS_OUTPUT_DIR)
    HWACCEL_DEVICE = format(args.device)
    # clear log file and video info file
    open(VIDEOS_OUTPUT_DIR + "/encoding.log", "w").close()
    open(VIDEOS_OUTPUT_DIR + "/info_video.json", "w").close()

    input_file = os.path.basename(format(args.input)) if args.input else ""
    path_file = '{}/{}'.format(VIDEOS_DIR, input_file)
    if os.access(path_file, os.F_OK) and os.stat(path_file).st_size > 0:
        # remove accent and space
        filename = ''.join(
            (
                c for c in unicodedata.normalize(
                    'NFD', input_file
                ) if unicodedata.category(c) != 'Mn'
            )
        )
        filename = filename.replace(' ', '_')
        os.rename('{}/{}'.format(VIDEOS_DIR, input_file),
                  '{}/{}'.format(VIDEOS_DIR, filename))
        msg += 'Encoding file {} \n'.format(filename)

        info_video = {}

        info_video = get_info_video(filename)
        msg += " \n"
        msg += json.dumps(info_video, indent=2)
        msg += " \n"
        for val in info_video:
            add_info_video(val, info_video[val])

        encode_result = launch_encode(info_video, filename)
        add_info_video("encode_result", encode_result)
        msg += "- fin de l'encodage : %s \n" % time.ctime()
        encode_log(msg)
    else:
        msg += "\n Wrong file or path %s " % path_file
        encode_log(msg)

"""
ffmpeg - decoders | grep cuvid
 V..... h264_cuvid           Nvidia CUVID H264 decoder(codec h264)
 V..... hevc_cuvid           Nvidia CUVID HEVC decoder(codec hevc)
 V..... mjpeg_cuvid          Nvidia CUVID MJPEG decoder(codec mjpeg)
 V..... mpeg1_cuvid          Nvidia CUVID MPEG1VIDEO decoder(codec mpeg1video)
 V..... mpeg2_cuvid          Nvidia CUVID MPEG2VIDEO decoder(codec mpeg2video)
 V..... mpeg4_cuvid          Nvidia CUVID MPEG4 decoder(codec mpeg4)
 V..... vc1_cuvid            Nvidia CUVID VC1 decoder(codec vc1)
 V..... vp8_cuvid            Nvidia CUVID VP8 decoder(codec vp8)
 V..... vp9_cuvid            Nvidia CUVID VP9 decoder(codec vp9)
"""
