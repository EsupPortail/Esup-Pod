from django.conf import settings
from django.utils.translation import ugettext_lazy as _
from django.core.mail import send_mail
from django.core.mail import mail_admins
from django.core.mail import mail_managers
from django.core.mail import EmailMultiAlternatives

from .models import EncodingStep
from .models import EncodingLog
from .models import Video

import os

DEBUG = getattr(settings, 'DEBUG', True)

TEMPLATE_VISIBLE_SETTINGS = getattr(
    settings,
    'TEMPLATE_VISIBLE_SETTINGS',
    {
        'TITLE_SITE': 'Pod',
        'TITLE_ETB': 'University name',
        'LOGO_SITE': 'img/logoPod.svg',
        'LOGO_ETB': 'img/logo_etb.svg',
        'LOGO_PLAYER': 'img/logoPod.svg',
        'LINK_PLAYER': '',
        'FOOTER_TEXT': ('',),
        'FAVICON': 'img/logoPod.svg',
        'CSS_OVERRIDE': '',
        'PRE_HEADER_TEMPLATE': '',
        'POST_FOOTER_TEMPLATE': '',
        'TRACKING_TEMPLATE': '',
    }
)

TITLE_SITE = getattr(TEMPLATE_VISIBLE_SETTINGS, 'TITLE_SITE', 'Pod')

DEFAULT_FROM_EMAIL = getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@univ.fr')

USE_ESTABLISHMENT = getattr(
    settings, 'USE_ESTABLISHMENT_FIELD', False)

MANAGERS = getattr(settings, 'MANAGERS', {})

SECURE_SSL_REDIRECT = getattr(settings, 'SECURE_SSL_REDIRECT', False)


# ##########################################################################
# ENCODE VIDEO : GENERIC FUNCTION
# ##########################################################################


def change_encoding_step(video_id, num_step, desc):
    encoding_step, created = EncodingStep.objects.get_or_create(
        video=Video.objects.get(id=video_id))
    encoding_step.num_step = num_step
    encoding_step.desc_step = desc
    encoding_step.save()
    if DEBUG:
        print("step: %d - desc: %s" % (
            num_step, desc
        ))


def add_encoding_log(video_id, log):
    encoding_log = EncodingLog.objects.get(
        video=Video.objects.get(id=video_id))
    encoding_log.log += "\n\n%s" % (log)
    encoding_log.save()
    if DEBUG:
        print(log)


def check_file(path_file):
    if os.access(path_file, os.F_OK) and os.stat(path_file).st_size > 0:
        return True
    return False

# ##########################################################################
# ENCODE VIDEO : CREATE OUTPUT DIR
# ##########################################################################


def create_outputdir(video_id, video_path):
    dirname = os.path.dirname(video_path)
    output_dir = os.path.join(dirname, "%04d" % video_id)
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    return output_dir

###############################################################
# EMAIL
###############################################################


def send_email(msg, video_id):
    subject = "[" + TITLE_SITE + \
        "] Error Encoding Video id:%s" % video_id
    message = "Error Encoding  video id : %s\n%s" % (
        video_id, msg)
    html_message = "<p>Error Encoding video id : %s</p><p>%s</p>" % (
        video_id,
        msg.replace('\n', "<br/>"))
    mail_admins(
        subject,
        message,
        fail_silently=False,
        html_message=html_message)


def send_email_transcript(video_to_encode):
    if DEBUG:
        print("SEND EMAIL ON TRANSCRIPTING COMPLETION")
    url_scheme = "https" if SECURE_SSL_REDIRECT else "http"
    content_url = "%s:%s" % (url_scheme, video_to_encode.get_full_url())
    subject = "[%s] %s" % (
        TITLE_SITE,
        _(u"Transcripting #%(content_id)s completed") % {
            'content_id': video_to_encode.id
        }
    )
    message = "%s\n%s\n\n%s\n%s\n%s\n" % (
        _("Hello"),
        _(u"The content “%(content_title)s” has been automatically transcript"
            + ", and is now available on %(site_title)s.") % {
            'content_title': video_to_encode.title,
            'site_title': TITLE_SITE
        },
        _(u"You will find it here:"),
        content_url,
        _("Regards")
    )
    full_message = message + "\n%s:%s\n%s:%s" % (
        _("Post by"),
        video_to_encode.owner,
        _("the"),
        video_to_encode.date_added
    )
    from_email = DEFAULT_FROM_EMAIL
    to_email = []
    to_email.append(video_to_encode.owner.email)
    html_message = ""

    html_message = '<p>%s</p><p>%s</p><p>%s<br><a href="%s"><i>%s</i></a>\
                </p><p>%s</p>' % (
        _("Hello"),
        _(u"The content “%(content_title)s” has been automatically transcript"
            + ", and is now available on %(site_title)s.") % {
            'content_title': '<b>%s</b>' % video_to_encode.title,
            'site_title': TITLE_SITE
        },
        _(u"You will find it here:"),
        content_url,
        content_url,
        _("Regards")
    )
    full_html_message = html_message + "<br/>%s:%s<br/>%s:%s" % (
        _("Post by"),
        video_to_encode.owner,
        _("the"),
        video_to_encode.date_added
    )

    if (
            USE_ESTABLISHMENT and
            MANAGERS and
            video_to_encode.owner.owner.establishment.lower() in dict(MANAGERS)
    ):
        bcc_email = []
        video_estab = video_to_encode.owner.owner.establishment.lower()
        manager = dict(MANAGERS)[video_estab]
        if type(manager) in (list, tuple):
            bcc_email = manager
        elif type(manager) == str:
            bcc_email.append(manager)
        msg = EmailMultiAlternatives(
            subject,
            message,
            from_email,
            to_email,
            bcc=bcc_email)
        msg.attach_alternative(html_message, "text/html")
        msg.send()
    else:
        mail_managers(
            subject, full_message, fail_silently=False,
            html_message=full_html_message)
        if not DEBUG:
            send_mail(
                subject,
                message,
                from_email,
                to_email,
                fail_silently=False,
                html_message=html_message,
            )


def send_email_encoding(video_to_encode):
    if DEBUG:
        print("SEND EMAIL ON ENCODING COMPLETION")
    url_scheme = "https" if SECURE_SSL_REDIRECT else "http"
    content_url = "%s:%s" % (url_scheme, video_to_encode.get_full_url())
    subject = "[%s] %s" % (
        TITLE_SITE,
        _(u"Encoding #%(content_id)s completed") % {
            'content_id': video_to_encode.id
        }
    )
    message = "%s\n%s\n\n%s\n%s\n%s\n" % (
        _("Hello"),
        _(u"The content “%(content_title)s” has been encoded to Web "
            + "formats, and is now available on %(site_title)s.") % {
            'content_title': video_to_encode.title,
            'site_title': TITLE_SITE
        },
        _(u"You will find it here:"),
        content_url,
        _("Regards")
    )
    full_message = message + "\n%s:%s\n%s:%s" % (
        _("Post by"),
        video_to_encode.owner,
        _("the"),
        video_to_encode.date_added
    )
    from_email = DEFAULT_FROM_EMAIL
    to_email = []
    to_email.append(video_to_encode.owner.email)
    html_message = ""

    html_message = '<p>%s</p><p>%s</p><p>%s<br><a href="%s"><i>%s</i></a>\
                </p><p>%s</p>' % (
        _("Hello"),
        _(u"The content “%(content_title)s” has been encoded to Web "
            + "formats, and is now available on %(site_title)s.") % {
            'content_title': '<b>%s</b>' % video_to_encode.title,
            'site_title': TITLE_SITE
        },
        _(u"You will find it here:"),
        content_url,
        content_url,
        _("Regards")
    )
    full_html_message = html_message + "<br/>%s:%s<br/>%s:%s" % (
        _("Post by"),
        video_to_encode.owner,
        _("the"),
        video_to_encode.date_added
    )

    if (
            USE_ESTABLISHMENT and
            MANAGERS and
            video_to_encode.owner.owner.establishment.lower() in dict(MANAGERS)
    ):
        bcc_email = []
        video_estab = video_to_encode.owner.owner.establishment.lower()
        manager = dict(MANAGERS)[video_estab]
        if type(manager) in (list, tuple):
            bcc_email = manager
        elif type(manager) == str:
            bcc_email.append(manager)
        msg = EmailMultiAlternatives(
            subject,
            message,
            from_email,
            to_email,
            bcc=bcc_email)
        msg.attach_alternative(html_message, "text/html")
        msg.send()
    else:
        mail_managers(
            subject, full_message, fail_silently=False,
            html_message=full_html_message)
        if not DEBUG:
            send_mail(
                subject,
                message,
                from_email,
                to_email,
                fail_silently=False,
                html_message=html_message,
            )
