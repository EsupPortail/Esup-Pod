"""Utils for Meeting module."""
from datetime import date, timedelta
from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.utils.translation import ugettext_lazy as _
from pod.main.views import TEMPLATE_VISIBLE_SETTINGS
from hashlib import sha1

import bleach

BBB_API_URL = getattr(settings, "BBB_API_URL", "")
BBB_SECRET_KEY = getattr(settings, "BBB_SECRET_KEY", "")

DEBUG = getattr(settings, "DEBUG", True)

DEFAULT_FROM_EMAIL = getattr(settings, "DEFAULT_FROM_EMAIL", "noreply@univ.fr")

MANAGERS = getattr(settings, "MANAGERS", {})

SECURE_SSL_REDIRECT = getattr(settings, "SECURE_SSL_REDIRECT", False)


def api_call(query, call):
    """Generate checksum for BBB API call."""
    checksum_val = sha1(str(call + query + BBB_SECRET_KEY).encode("utf-8")).hexdigest()
    result = "%s&checksum=%s" % (query, checksum_val)
    return result


def parseXmlToJson(xml, sub=False):
    """Parse XML to JSON format."""
    response = {}
    counter = 1
    for child in list(xml):
        index = child.tag
        if response.get(child.tag):
            temp_child = response[child.tag]
            response[child.tag + "__%s" % counter] = temp_child
            del response[child.tag]
        if response.get(child.tag + "__%s" % counter):
            counter += 1
            index = child.tag + "__%s" % counter

        if len(list(child)) > 0:
            response[index] = parseXmlToJson(child, sub=True)
        else:
            response[index] = child.text or ""
    return response


def slash_join(*args):
    """Add slash to arguments."""
    return "/".join(arg.strip("/") for arg in args)


def get_weekday_in_nth_week(year, month, nth_week, week_day):
    """Return the date corresponding to the nth weekday of a month.

    e.g. 3rd Friday of July 2022 is July 15, 2002 so:
    > get_weekday_in_nth_week(2022, 7, 3, 4)
    date(2022, 7, 15)
    """
    new_date = date(year, month, 1)
    delta = (week_day - new_date.weekday()) % 7
    new_date += timedelta(days=delta)
    new_date += timedelta(weeks=nth_week - 1)
    return new_date


def get_nth_week_number(original_date):
    """Return the number of the week within the month for the date passed in argument.

    e.g. July 15, 2022 is the 3rd Friday of the month of Juy 2022 so:
    > get_nth_week_number(date(2022, 7, 15))
    3
    """
    first_day = original_date.replace(day=1)
    first_week_last_day = 7 - first_day.weekday()
    day_of_month = original_date.day
    if day_of_month < first_week_last_day:
        return 1
    nb_weeks = 1 + (day_of_month - first_week_last_day) // 7
    if first_day.weekday() <= original_date.weekday():
        nb_weeks += 1
    return nb_weeks


def send_email_recording_ready(meeting):
    """Send an email when a recording was saved and available on Pod."""
    if DEBUG:
        print("SEND EMAIL WHEN RECORDING READY")

    url_scheme = "https" if SECURE_SSL_REDIRECT else "http"
    content_url = "%s:%s" % (url_scheme, meeting.get_recordings_full_url())

    subject = "[%s] %s" % (
        TEMPLATE_VISIBLE_SETTINGS.get("TITLE_SITE"),
        _("A new Big Blue Button recording for '%(name)s' meeting is available")
        % {"name": meeting.name},
    )

    from_email = DEFAULT_FROM_EMAIL

    to_email = [meeting.owner.email]

    html_message = (
        '<p>%s</p><p>%s</p><p>%s<br><a href="%s"><i>%s</i></a></p><p>%s</p>'
        % (
            _("Hello,"),
            _(
                "A new Big Blue Button recording for “%(content_title)s” meeting"
                + " is now available on %(site_title)s."
            )
            % {
                "content_title": "<b>%s</b>" % meeting.name,
                "site_title": TEMPLATE_VISIBLE_SETTINGS.get("TITLE_SITE"),
            },
            _("You will find it here:"),
            content_url,
            content_url,
            _("Regards."),
        )
    )

    text_message = bleach.clean(html_message, tags=[], strip=True)

    msg = EmailMultiAlternatives(subject, text_message, from_email, to_email)
    msg.attach_alternative(html_message, "text/html")

    if DEBUG:
        print(text_message)

    msg.send()
