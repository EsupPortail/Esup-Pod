import os

from django.conf import settings
from pod.video_encode.models import EncodingStep
from pod.video_encode.models import EncodingLog
from pod.video.models import Video


DEBUG = getattr(settings, "DEBUG", True)

TEMPLATE_VISIBLE_SETTINGS = getattr(
    settings,
    "TEMPLATE_VISIBLE_SETTINGS",
    {
        "TITLE_SITE": "Pod",
        "TITLE_ETB": "University name",
        "LOGO_SITE": "img/logoPod.svg",
        "LOGO_ETB": "img/esup-pod.svg",
        "LOGO_PLAYER": "img/pod_favicon.svg",
        "LINK_PLAYER": "",
        "FOOTER_TEXT": ("",),
        "FAVICON": "img/pod_favicon.svg",
        "CSS_OVERRIDE": "",
        "PRE_HEADER_TEMPLATE": "",
        "POST_FOOTER_TEMPLATE": "",
        "TRACKING_TEMPLATE": "",
    },
)

__TITLE_SITE__ = (
    TEMPLATE_VISIBLE_SETTINGS["TITLE_SITE"]
    if (TEMPLATE_VISIBLE_SETTINGS.get("TITLE_SITE"))
    else "Pod"
)

DEFAULT_FROM_EMAIL = getattr(settings, "DEFAULT_FROM_EMAIL", "noreply@univ.fr")

USE_ESTABLISHMENT_FIELD = getattr(settings, "USE_ESTABLISHMENT_FIELD", False)

MANAGERS = getattr(settings, "MANAGERS", {})

SECURE_SSL_REDIRECT = getattr(settings, "SECURE_SSL_REDIRECT", False)
VIDEOS_DIR = getattr(settings, "VIDEOS_DIR", "videos")


# ##########################################################################
# ENCODE VIDEO : GENERIC FUNCTIONS
# ##########################################################################


def change_encoding_step(video_id, num_step, desc):
    """Change encoding step."""
    encoding_step, created = EncodingStep.objects.get_or_create(
        video=Video.objects.get(id=video_id)
    )
    encoding_step.num_step = num_step
    encoding_step.desc_step = desc[:255]
    encoding_step.save()
    if DEBUG:
        print("step: %d - desc: %s" % (num_step, desc))


def add_encoding_log(video_id, log):
    """Add message in video_id encoding log."""
    encoding_log, created = EncodingLog.objects.get_or_create(
        video=Video.objects.get(id=video_id)
    )
    if created:
        encoding_log.log = log
    else:
        encoding_log.log += "\n\n%s" % log
    encoding_log.save()
    if DEBUG:
        print(log)


def check_file(path_file):
    """Check if path_file is accessible and is not null."""
    if os.access(path_file, os.F_OK) and os.stat(path_file).st_size > 0:
        return True
    return False


def create_outputdir(video_id, video_path):
    """ENCODE VIDEO: CREATE OUTPUT DIR."""
    dirname = os.path.dirname(video_path)
    output_dir = os.path.join(dirname, "%04d" % video_id)
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    return output_dir

