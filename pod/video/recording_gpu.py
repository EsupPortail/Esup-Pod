import os
import subprocess
import json
import argparse
import time

# python3 /home/nicolas.can/pod-encoding/record_gpu.py
# --device ${CUDA_VISIBLE_DEVICES} --dir "/tmp/recording-39"
# --input_presenter "/tmp/recording-39/presenter_source.webm"
# --input_presentation "/tmp/recording-39/presentation_source.webm" --job ${SLURM_JOB_ID}
# --name "recording-39" --debug "True" --pip "pipb" --subtime "-ss 1.2 -to 10.09 "

__author__ = "Nicolas CAN <nicolas.can@univ-lille.fr>"
__license__ = "LGPL v3"

DEBUG = False
VIDEOS_DIR = "videos"
FFPROBE = "ffprobe"
FFMPEG = "time ffmpeg"
GET_INFO_VIDEO = str(
    "%(ffprobe)s -v quiet -show_format -show_streams "
    + "-select_streams v:0 -print_format json -i %(source)s"
)
FFMPEG_NB_THREADS = 0
"""
FFMPEG_STATIC_PARAMS = str(
    " -c:a aac -ar 48000 -strict experimental "
    + "-profile:v high -pix_fmt yuv420p -preset slow -qmin 20 -qmax 50 "
    + '-sc_threshold 0 -force_key_frames "expr:gte(t,n_forced*1)" '
    + "-max_muxing_queue_size 4000 "
    + "-deinterlace -threads %(nb_threads)s "
)
"""

FFMPEG_STATIC_PARAMS = (
    " -c:a aac -ar 48000 -c:v h264 -profile:v high -pix_fmt yuv420p -crf 22 "
    + '-sc_threshold 0 -force_key_frames "expr:gte(t,n_forced*1)" '
    + "-max_muxing_queue_size 4000 "
    + "-deinterlace -threads 0 "
)
FFMPEG_MISC_PARAMS = " -hide_banner -y -vsync 0 "
FFMPEG_CRF = 22
FFMPEG_MISC_PARAMS_GPU = " -hide_banner -y -vsync 0 -hwaccel_device %(hwaccel_device)s \
    -hwaccel cuvid -c:v %(codec)s_cuvid "
LIST_CODEC = ("h264", "hevc", "mjpeg", "mpeg1", "mpeg2", "mpeg4", "vc1", "vp8", "vp9")


def encode_log(msg):
    if DEBUG:
        print(msg)
    with open(VIDEOS_DIR + "/encoding.log", "a") as f:
        f.write("\n")
        f.write(msg)
        f.write("\n")


def get_video_info(command):
    ffproberesult = subprocess.run(
        command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT
    )
    return json.loads(ffproberesult.stdout.decode("utf-8"))


def get_sub_cmd(height_presentation_video, height_presenter_video, presenter):
    min_height = min([height_presentation_video, height_presenter_video])
    subcmd = ""
    if presenter == "pipb":
        # trouver la bonne hauteur en fonction de la video de presentation
        height = (
            height_presentation_video
            if (height_presentation_video % 2) == 0
            else height_presentation_video + 1
        )
        # ffmpeg -y -i presentation_source.webm -i presenter_source.webm \
        # -c:v libx264 -filter_complex "[0:v]scale=-2:720[pres];[1:v]scale=-2:180[pip];\
        # [pres][pip]overlay=W-w-10:H-h-10:shortest=1" \
        # -vsync 0 outputVideo.mp4
        subcmd = (
            " -filter_complex "
            + '"[0:v]scale=-2:%(height)s[pres];[1:v]scale=-2:%(sh)s[pip];'
            % {"height": height, "sh": height / 4}
            + '[pres][pip]overlay=W-w-10:H-h-10:shortest=1" -vsync 0 '
        )
    if presenter == "piph":
        # trouver la bonne hauteur en fonction de la video de presentation
        height = (
            height_presentation_video
            if (height_presentation_video % 2) == 0
            else height_presentation_video + 1
        )
        # ffmpeg -y -i presentation_source.webm -i presenter_source.webm \
        # -c:v libx264 -filter_complex "[0:v]scale=-2:720[pres];[1:v]scale=-2:180[pip];\
        # [pres][pip]overlay=W-w-10:H-h-10:shortest=1" \
        # -vsync 0 outputVideo.mp4
        subcmd = (
            " -filter_complex "
            + '"[0:v]scale=-2:%(height)s[pres];[1:v]scale=-2:%(sh)s[pip];'
            % {"height": height, "sh": height / 4}
            + '[pres][pip]overlay=W-w-10:10:shortest=1" -vsync 0 '
        )
    if presenter == "mid":
        height = min_height if (min_height % 2) == 0 else min_height + 1
        subcmd = (
            " -filter_complex "
            + '"[0:v]scale=-2:%(height)s[left];[1:v]scale=-2:%(height)s[right];'
            % {"height": height}
            + '[left][right]hstack" -vsync 0 '
        )

    return subcmd


def get_height(info):
    in_height = 0
    if len(info["streams"]) > 0 and info["streams"][0].get("height"):
        in_height = info["streams"][0]["height"]
    return in_height


def get_codec_name(info):
    codec_name = ""
    if len(info["streams"]) > 0 and info["streams"][0].get("codec_name"):
        codec_name = info["streams"][0]["codec_name"]
    return codec_name


def encode_video_studio(
    presenter_source, presentation_source, subtime, presenter, video_output
):
    input_video = ""
    codec_name = ""
    if presenter_source:
        input_video = '-i "' + presenter_source + '" '
        command = GET_INFO_VIDEO % {
            "ffprobe": FFPROBE,
            "source": '"' + presenter_source + '" ',
        }
        info_presenter_video = get_video_info(command)
        codec_name = get_codec_name(info_presenter_video)

    if presentation_source:
        input_video = '-i "' + presentation_source + '" '
        command = GET_INFO_VIDEO % {
            "ffprobe": FFPROBE,
            "source": '"' + presentation_source + '" ',
        }
        info_presentation_video = get_video_info(command)
        codec_name = get_codec_name(info_presenter_video)

    if presenter_source and presentation_source:
        # to put it in the right order
        input_video = '-i "' + presentation_source + '" -i "' + presenter_source + '" '

        subcmd = get_sub_cmd(
            get_height(info_presentation_video),
            get_height(info_presenter_video),
            presenter,
        )
    else:
        subcmd = " -vsync 0 "
    subcmd += " -movflags +faststart -f mp4 "
    static_params = FFMPEG_STATIC_PARAMS % {
        "nb_threads": FFMPEG_NB_THREADS,
        "crf": FFMPEG_CRF,
    }
    msg = launch_encode_video_studio(
        input_video, subtime + static_params + subcmd, video_output, codec_name
    )
    return msg


def launch_encode_video_studio(input_video, subcmd, video_output, codec_name):
    """Encode video for studio."""
    msg = ""
    misc_params = FFMPEG_MISC_PARAMS
    """
    if codec_name in LIST_CODEC:
        misc_params = FFMPEG_MISC_PARAMS_GPU % {
            "hwaccel_device": HWACCEL_DEVICE,
            "codec": codec_name,
        }
    """
    ffmpegStudioCommand = "%s %s %s %s %s" % (
        FFMPEG,
        misc_params,
        input_video,
        subcmd,
        video_output,
    )
    msg += "- %s\n" % ffmpegStudioCommand
    ffmpegstudio = subprocess.run(
        ffmpegStudioCommand, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT
    )
    msg += "\n\ffmpegstudio:\n\n %s " % ffmpegstudio.stdout
    msg += "\n- Encoding Mp4: %s" % time.ctime()
    if DEBUG:
        print(msg)
    return msg


if __name__ == "__main__":
    msg = "--> Main \n"
    msg += "- lancement cycle encodage : %s \n" % time.ctime()
    parser = argparse.ArgumentParser(description="Running encoding video.")
    parser.add_argument("--device", required=True, help="CUDA_VISIBLE_DEVICES")
    parser.add_argument("--dir", required=True, help="base dir to encode")
    parser.add_argument(
        "--input_presenter", required=False, help="name of input presenter file to encode"
    )
    parser.add_argument(
        "--input_presentation",
        required=False,
        help="name of input presentation file to encode",
    )
    parser.add_argument("--job", required=False, help="the ID of job")
    parser.add_argument("--name", required=False, help="the name of job")
    parser.add_argument("--debug", required=False, help="run job in debug mode")
    parser.add_argument("--pip", required=True, help="pip presenter : mid, piph or pipb")
    parser.add_argument("--subtime", required=False, help="run job in debug mode")
    args = parser.parse_args()
    msg += "Using device {} \n".format(args.device)
    msg += "Using job {} \n".format(args.job)
    msg += "Using name {} \n".format(args.name)

    # --dir /workdir/nicolas.can//encoding/encoding-12689
    # --input videos/fa131629[...]b9a2424/clip-pod.mp4

    DEBUG = True if args.debug and args.debug == "True" else False

    subtime = args.subtime if args.subtime else ""

    VIDEOS_DIR = args.dir if args.dir else "videos"

    if not os.path.exists(VIDEOS_DIR):
        os.makedirs(VIDEOS_DIR)
    HWACCEL_DEVICE = format(args.device)
    # clear log file and video info file
    open(VIDEOS_DIR + "/encoding.log", "w").close()

    video_output = os.path.join(VIDEOS_DIR, "output.mp4")

    file_input_presenter = format(args.input_presenter) if args.input_presenter else None
    file_input_presentation = (
        format(args.input_presentation) if args.input_presentation else None
    )
    print(file_input_presenter, file_input_presentation)
    presenter_source = None
    presentation_source = None

    if (
        file_input_presenter
        and os.access(file_input_presenter, os.F_OK)
        and os.stat(file_input_presenter).st_size > 0
    ):
        presenter_source = file_input_presenter

    if (
        file_input_presentation
        and os.access(file_input_presentation, os.F_OK)
        and os.stat(file_input_presentation).st_size > 0
    ):
        presentation_source = file_input_presentation

    if presenter_source is None and presentation_source is None:
        msg += "\nALERT : NO FILE TO ENCODE\n"
    else:
        msg += encode_video_studio(
            presenter_source, presentation_source, subtime, format(args.pip), video_output
        )

    msg += "- fin de l'encodage : %s \n" % time.ctime()
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
