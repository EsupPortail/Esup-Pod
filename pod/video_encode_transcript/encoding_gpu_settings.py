# manage setting to encode video with gpu
FFMPEG_USE_GPU = False
FFMPEG_CMD_GPU = "ffmpeg -hwaccel_device 0 -hwaccel_output_format cuda -hwaccel cuda"
FFMPEG_PRESET_GPU = "p6"
FFMPEG_LEVEL_GPU = 0

FFMPEG_INPUT_GPU = '-hide_banner -threads %(nb_threads)s -i "%(input)s" '

FFMPEG_LIBX_GPU = "h264_nvenc"
FFMPEG_MP4_ENCODE_GPU = (
    '%(cut)s -map 0:v:0 %(map_audio)s -c:v %(libx)s  -vf "scale_cuda=-2:%(height)s:interp_algo=bicubic:format=yuv420p" '
    + "-preset %(preset)s -profile:v %(profile)s "
    + "-level %(level)s "
    + "-forced-idr 1 "
    + "-b:v %(maxrate)s -maxrate %(maxrate)s -bufsize %(bufsize)s -rc vbr -rc-lookahead 20 -bf 1 "
    + '-force_key_frames "expr:gte(t,n_forced*1)" '
    + '-c:a aac -ar 48000 -b:a %(ba)s -movflags faststart -y -fps_mode passthrough "%(output)s" '
)
FFMPEG_HLS_COMMON_PARAMS_GPU = (
    "%(cut)s "
    + "-c:v %(libx)s -preset %(preset)s -profile:v %(profile)s "
    + "-level %(level)s "
    + "-forced-idr 1 "
    + '-force_key_frames "expr:gte(t,n_forced*1)" '
    + "-c:a aac -ar 48000 "
)
FFMPEG_HLS_ENCODE_PARAMS_GPU = (
    '-vf "scale_cuda=-2:%(height)s:interp_algo=bicubic:format=yuv420p" -b:v %(maxrate)s -maxrate %(maxrate)s -bufsize %(bufsize)s -b:a:0 %(ba)s -rc vbr -rc-lookahead 20 -bf 1 '
    + "-hls_playlist_type vod -hls_time %(hls_time)s  -hls_flags single_file "
    + '-master_pl_name "livestream%(height)s.m3u8" '
    + '-y "%(output)s" '
)

FFMPEG_CREATE_THUMBNAIL_GPU = (
    '-vf "select=between(t\,0\,%(duration)s)*eq(pict_type\,PICT_TYPE_I),thumbnail_cuda=2,scale_cuda=-2:720:interp_algo=bicubic:format=yuv420p,hwdownload,format=yuv420p" -frames:v %(nb_thumbnail)s -vsync vfr "%(output)s_%%04d.png"'
)

#FFMPEG_CREATE_OVERVIEW_GPU = (
#    " -vsync vfr -vf fps=(%(image_count)s/%(duration)s),scale_cuda=%(width)s:%(height)s:interp_algo=bicubic:format=yuv420p,hwdownload,tile=%(image_count)sx1,format=yuv420p -frames:v 1 '%(output)s' "
#)
