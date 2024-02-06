# manage setting to encode video
FFMPEG_CMD = "ffmpeg"
FFPROBE_CMD = "ffprobe"
FFMPEG_CRF = 20  # -crf 20 -maxrate 3M -bufsize 6M
FFMPEG_PRESET = "slow"
FFMPEG_PROFILE = "high"
FFMPEG_LEVEL = 3
FFMPEG_HLS_TIME = 2

FFPROBE_GET_INFO = (
    "%(ffprobe)s -v quiet -show_format -show_streams %(select_streams)s "
    + "-print_format json -i %(source)s"
)

FFMPEG_INPUT = '-hide_banner -threads %(nb_threads)s -i "%(input)s" '

FFMPEG_STUDIO_COMMAND = (
    " -hide_banner -threads %(nb_threads)s %(input)s %(subtime)s"
    + " -c:a aac -ar 48000 -c:v h264 -profile:v high -pix_fmt yuv420p"
    + " -crf %(crf)s -sc_threshold 0 -force_key_frames"
    + ' "expr:gte(t,n_forced*1)" -max_muxing_queue_size 4000 -deinterlace '
)

FFMPEG_LIBX = "libx264"
FFMPEG_MP4_ENCODE = (
    '%(cut)s -map 0:v:0 %(map_audio)s -c:v %(libx)s  -vf "scale=-2:%(height)s" '
    + "-preset %(preset)s -profile:v %(profile)s "
    + "-pix_fmt yuv420p -level %(level)s -crf %(crf)s "
    + "-maxrate %(maxrate)s -bufsize %(bufsize)s "
    + '-sc_threshold 0 -force_key_frames "expr:gte(t,n_forced*1)" '
    + "-max_muxing_queue_size 4000 "
    + '-c:a aac -ar 48000 -b:a %(ba)s -movflags faststart -y -vsync 0 "%(output)s" '
)
# https://gist.github.com/Andrey2G/78d42b5c87850f8fbadd0b670b0e6924
FFMPEG_HLS_COMMON_PARAMS = (
    "%(cut)s "
    + "-c:v %(libx)s -preset %(preset)s -profile:v %(profile)s -pix_fmt yuv420p "
    + "-level %(level)s -crf %(crf)s -sc_threshold 0 "
    + '-force_key_frames "expr:gte(t,n_forced*1)" '
    + "-c:a aac -ar 48000 -max_muxing_queue_size 4000 "
)
FFMPEG_HLS_ENCODE_PARAMS = (
    '-vf "scale=-2:%(height)s" -maxrate %(maxrate)s -bufsize %(bufsize)s -b:a:0 %(ba)s '
    + "-hls_playlist_type vod -hls_time %(hls_time)s  -hls_flags single_file "
    + '-master_pl_name "livestream%(height)s.m3u8" '
    + '-y "%(output)s" '
)

# FFMPEG_MP3_ENCODE = '-vn -b:a %(audio_bitrate)s -f mp3 -y "%(output)s" '
FFMPEG_MP3_ENCODE = '%(cut)s -vn -codec:a libmp3lame -qscale:a 2 -y "%(output)s" '
# In our example above, we selected -qscale:a 2, meaning we used LAME's option -V 2,
# which gives us a VBR MP3 audio stream with an average stereo bitrate of 170-210 kBit/s.
FFMPEG_M4A_ENCODE = '%(cut)s -vn -c:a aac -b:a %(audio_bitrate)s "%(output)s" '
FFMPEG_NB_THREADS = 0
FFMPEG_AUDIO_BITRATE = "192k"

FFMPEG_EXTRACT_THUMBNAIL = '-map 0:%(index)s -an -c:v copy -y  "%(output)s" '

FFMPEG_NB_THUMBNAIL = 3
# FFMPEG_CREATE_THUMBNAIL =
#  '-map 0:%(index)s -vframes 1 -an -ss %(time)s -y "%(output)s" '
FFMPEG_CREATE_THUMBNAIL = (
    '-vf "fps=1/(%(duration)s/%(nb_thumbnail)s)" -vsync vfr "%(output)s_%%04d.png"'
)
FFMPEG_EXTRACT_SUBTITLE = '-map 0:%(index)s -f webvtt -y  "%(output)s" '

FFMPEG_DRESSING_OUTPUT = ' -c:v libx264 -y -vsync 0 "%(output)s" '
FFMPEG_DRESSING_INPUT = ' -i "%(input)s"'
FFMPEG_DRESSING_FILTER_COMPLEX = ' -filter_complex "%(filter)s" '
FFMPEG_DRESSING_WATERMARK = (
    " [1]format=rgba,colorchannelmixer=aa=%(opacity)s[logo]; "
    + " [logo][vid]scale2ref=oh*mdar:ih*0.1[logo][video2]; "
    + " [video2][logo]%(position)s%(name_out)s "
)
FFMPEG_DRESSING_SCALE = (
    "[%(number)s]scale=-1:%(height)s:force_original_aspect_ratio= "
    + "decrease,pad=ceil(ih*16/9):ih:(ow-iw)/2:(oh-ih)/2[%(name)s]"
)
FFMPEG_DRESSING_CONCAT = "%(params)sconcat=n=%(number)s:v=1:a=1:unsafe=1[v][a]"

VIDEO_RENDITIONS = [
    {
        "resolution": "640x360",
        "minrate": "500k",
        "video_bitrate": "750k",
        "maxrate": "1000k",
        "audio_bitrate": "96k",
        "encoding_resolution_threshold": 0,
        "encode_mp4": True,
        "sites": [1],
    },
    {
        "resolution": "1280x720",
        "minrate": "1000k",
        "video_bitrate": "2000k",
        "maxrate": "3000k",
        "audio_bitrate": "128k",
        "encoding_resolution_threshold": 0,
        "encode_mp4": True,
        "sites": [1],
    },
    {
        "resolution": "1920x1080",
        "minrate": "2000k",
        "video_bitrate": "3000k",
        "maxrate": "4500k",
        "audio_bitrate": "192k",
        "encoding_resolution_threshold": 0,
        "encode_mp4": False,
        "sites": [1],
    },
]
