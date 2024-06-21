# manage setting to encode video with gpu
FFMPEG_USE_GPU = False
FFMPEG_CMD = "ffmpeg -hwaccel_device 0 -hwaccel_output_format cuda -hwaccel cuda"
FFMPEG_PRESET = "p6"

FFMPEG_INPUT = '-hide_banner -threads %(nb_threads)s -i "%(input)s" '

FFMPEG_LIBX = "h264_nvenc"
FFMPEG_MP4_ENCODE = (
    '%(cut)s -map 0:v:0 %(map_audio)s -c:v %(enc_gpu)s  -vf "scale_cuda=-2:%(height)s:interp_algo=bicubic:format=yuv420p" '
    + "-preset %(preset)s -profile:v %(profile)s "
    + "-level %(level)s "
    + "-forced-idr 1 "
    + "-b:v %(maxrate)s -maxrate %(maxrate)s -bufsize %(bufsize)s -rc vbr -rc-lookahead 20 -bf 1 "
    + '-force_key_frames "expr:gte(t,n_forced*1)" '
    + '-c:a aac -ar 48000 -b:a %(ba)s -movflags faststart -y -fps_mode passthrough "%(output)s" '
)
FFMPEG_HLS_COMMON_PARAMS = (
    "%(cut)s "
    + "-c:v %(libx)s -preset %(preset)s -profile:v %(profile)s "
    + "-level %(level)s "
    + "-forced-idr 1 "
    + '-force_key_frames "expr:gte(t,n_forced*1)" '
    + "-c:a aac -ar 48000 "
)
FFMPEG_HLS_ENCODE_PARAMS = (
    '-vf "scale_cuda=-2:%(height)s:interp_algo=bicubic:format=yuv420p" -b:v %(maxrate)s -maxrate %(maxrate)s -bufsize %(bufsize)s -b:a:0 %(ba)s -rc vbr -rc-lookahead 20 -bf 1 '
    + "-hls_playlist_type vod -hls_time %(hls_time)s  -hls_flags single_file "
    + '-master_pl_name "livestream%(height)s.m3u8" '
    + '-y "%(output)s" '
)

FFMPEG_CREATE_THUMBNAIL = (
    '-vf "select=between(t\,0\,%(duration)s)*eq(pict_type\,PICT_TYPE_I)" -frames:v %(nb_thumbnail)s -vsync vfr "%(output)s_%%04d.png"'
)
