from webpush import send_user_notification
from django.templatetags.static import static


DEFAULT_ICON = static('img/icon_x1024.png')


def notify_user(user, title, message, url=None, icon=None):
    """Fills the payload to send a webpush notification to users devices."""
    payload = {
        "head": title,
        "body": message,
        "url": url,
        "icon": icon or DEFAULT_ICON,
    }
    send_user_notification(user=user, payload=payload, ttl=1000)
