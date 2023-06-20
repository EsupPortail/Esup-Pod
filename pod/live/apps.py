from django.apps import AppConfig
from django.db.models.signals import post_migrate, pre_migrate
from django.db import connection

# from django.db.utils import OperationalError
from django.utils import timezone
from datetime import datetime
from django.utils.translation import gettext_lazy as _

__EVENT_DATA__ = {}


def set_default_site(sender, **kwargs):
    from pod.live.models import Building
    from django.contrib.sites.models import Site

    for build in Building.objects.all():
        if len(build.sites.all()) == 0:
            build.sites.add(Site.objects.get_current())
            build.save()


class LiveConfig(AppConfig):
    name = "pod.live"
    default_auto_field = "django.db.models.BigAutoField"
    # event_data = {}
    verbose_name = _("Lives")

    def ready(self):
        post_migrate.connect(set_default_site, sender=self)
        pre_migrate.connect(self.save_previous_data, sender=self)
        post_migrate.connect(self.send_previous_data, sender=self)

    def save_previous_data(self, sender, **kwargs):
        results = []
        try:
            with connection.cursor() as c:
                c.execute("SELECT id, start_date, start_time, end_time FROM live_event")
                results = c.fetchall()
                for res in results:
                    __EVENT_DATA__["%s" % res[0]] = [res[1], res[2], res[3]]
        except Exception:  # OperationalError or MySQLdb.ProgrammingError
            pass  # print('OperationalError: ', oe)

    def send_previous_data(self, sender, **kwargs):
        from .models import Event

        for id in __EVENT_DATA__:
            try:
                evt = Event.objects.get(id=id)
                d_start = datetime.combine(__EVENT_DATA__[id][0], __EVENT_DATA__[id][1])
                d_start = timezone.make_aware(d_start)
                evt.start_date = d_start
                d_fin = datetime.combine(__EVENT_DATA__[id][0], __EVENT_DATA__[id][2])
                d_fin = timezone.make_aware(d_fin)
                evt.end_date = d_fin
                evt.save()
            except Event.DoesNotExist:
                print("Event not found: %s" % id)
