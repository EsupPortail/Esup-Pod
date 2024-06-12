"""Esup-Pod Live apps."""

from django.apps import AppConfig
from django.db.models.signals import post_migrate, pre_migrate
from django.db import connection

# from django.db.utils import OperationalError
from django.utils import timezone
from datetime import datetime
from django.utils.translation import gettext_lazy as _

__EVENT_DATA__ = {}


def set_default_site(sender, **kwargs) -> None:
    """Set a default Site for Building not having one."""
    from pod.live.models import Building
    from django.contrib.sites.models import Site

    for build in Building.objects.all():
        if build.sites.count() == 0:
            build.sites.add(Site.objects.get_current())
            build.save()


def add_default_opencast(sender, **kwargs) -> None:
    """Add the key 'use_opencast' with value False, in the json conf of the Broadcaster if not present."""
    from pod.live.models import Broadcaster

    brds = Broadcaster.objects.filter(
        piloting_implementation="SMP", piloting_conf__isnull=False
    ).all()
    for brd in brds:
        conf = brd.piloting_conf
        if "use_opencast" not in conf:
            brd.piloting_conf = conf.replace("}", ',"use_opencast":"false"}')
            brd.save()


def save_previous_data(sender, **kwargs) -> None:
    """Save all live events if model has date and time in different fields."""
    results = []
    try:
        with connection.cursor() as c:
            c.execute("SELECT id, start_date, start_time, end_time FROM live_event")
            results = c.fetchall()
            for res in results:
                __EVENT_DATA__["%s" % res[0]] = [res[1], res[2], res[3]]
    except Exception:  # OperationalError or MySQLdb.ProgrammingError
        pass  # print('OperationalError: ', oe)


def send_previous_data(sender, **kwargs) -> None:
    """Set start and end dates with date + time to all saved events."""
    from .models import Event

    for data_id in __EVENT_DATA__:
        try:
            evt = Event.objects.get(id=data_id)
            d_start = datetime.combine(
                __EVENT_DATA__[data_id][0], __EVENT_DATA__[data_id][1]
            )
            d_start = timezone.make_aware(d_start)
            evt.start_date = d_start
            d_fin = datetime.combine(
                __EVENT_DATA__[data_id][0], __EVENT_DATA__[data_id][2]
            )
            d_fin = timezone.make_aware(d_fin)
            evt.end_date = d_fin
            evt.save()
        except Event.DoesNotExist:
            print("Event not found: %s" % data_id)


class LiveConfig(AppConfig):
    """Config file for live app."""

    name = "pod.live"
    default_auto_field = "django.db.models.BigAutoField"
    # event_data = {}
    verbose_name = _("Lives")

    def ready(self) -> None:
        """Init tasks."""
        pre_migrate.connect(save_previous_data, sender=self)
        post_migrate.connect(add_default_opencast, sender=self)
        post_migrate.connect(set_default_site, sender=self)
        post_migrate.connect(send_previous_data, sender=self)
