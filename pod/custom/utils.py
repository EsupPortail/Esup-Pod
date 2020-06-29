from django.utils import timezone
import re
from dateutil.relativedelta import relativedelta


def remaining_days(del_date):
    return "%dj" % ((del_date - timezone.now()).days)


def remaining_months(del_date):
    now = timezone.now()
    diff = ((del_date.year - now.year)*12 +
            del_date.month - now.month)
    if (del_date.day - now.day) < 0:
        return "-%dm" % diff
    elif (del_date.day - now.day) > 0:
        return "+%dm" % diff
    else:
        return "%dm" % diff


def remaining_weeks(del_date):
    now = timezone.now()
    diff = ((del_date - now).days / 7)
    if diff > 1.0:
        return "+%ds" % diff
    else:
        return "%ds" % diff


def add_day(date, nb):
    return (date + relativedelta(days=nb)).date()


def add_month(date, nb, v):
    return (date + relativedelta(months=nb)).date()


# Retourne toutes les vidéos obsolètes ou bientôt selon
# la date de notification la plus élévée
# ex: si on doit notifier l'utilisateur 3mois avant, puis 1mois avant
# l'obsolescence de sa video, la fonction retournera
# toutes les videos dont le temps restant avant suppression
# est égale ou inferieur à 3mois
def filter_obsoletes_videos(model, remainings_times):
    # get the biggest remaining time
    all_videos = [
            v for v in model.objects.all() if(
                v.videotodelete_set.all().count() == 0 and
                v.date_delete)]
    remainings_times = ", ".join(remainings_times)
    months = re.findall(r"\dm", remainings_times)
    weeks = re.findall(r"\ds", remainings_times)
    days = re.findall(r"\dj", remainings_times)
    times = months if months else weeks
    times = times if times else days
    biggest_time = max(times)
    biggest_nb = int(re.findall(r"\d+", max(times))[0])
    now = timezone.now()
    if "m" in biggest_time:
        return [v for v in all_videos if(
            v.date_delete.date() <= add_month(
                now, biggest_nb, v))]
    elif "s" in biggest_time:
        return [v for v in all_videos if(
            v.date_delete.date() <= add_day(
                now, biggest_nb*7))]
    elif "j" in biggest_time:
        return [v for v in all_videos if(
            v.date_delete <= add_day(now, biggest_nb)
            )]
    return all_videos
