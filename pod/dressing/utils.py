import os

from django.conf import settings


def get_position_value(position, height):
    height = str(float(height) * 0.05)
    if position == 'top_right':
        return 'overlay=main_w-overlay_w-' + height + ':' + height
    elif position == 'top_left':
        return 'overlay=' + height + ':' + height
    elif position == 'bottom_right':
        return 'overlay=main_w-overlay_w-' + height + ':main_h-overlay_h-' + height
    elif position == 'bottom_left':
        return 'overlay=' + height + ':main_h-overlay_h-' + height


def get_dressing_input(dressing, FFMPEG_DRESSING_INPUT):
    command = ''
    if dressing.watermark:
        command += FFMPEG_DRESSING_INPUT % {
            "input": os.path.join(settings.BASE_DIR, dressing.watermark.file.url[1:])
        }
    if dressing.opening_credits:
        command += FFMPEG_DRESSING_INPUT % {
            "input": os.path.join(settings.MEDIA_ROOT,
                                  str(dressing.opening_credits.video))
        }
    if dressing.ending_credits:
        command += FFMPEG_DRESSING_INPUT % {
            "input": os.path.join(settings.MEDIA_ROOT, str(dressing.ending_credits.video))
        }
    return command
