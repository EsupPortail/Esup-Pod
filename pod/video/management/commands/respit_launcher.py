import importlib
from datetime import datetime, timedelta
from unicodedata import category

from pod.custom.settings_local import RESPIT_MODEL
from pod.video.models import Video
#https://docs.djangoproject.com/fr/6.0/howto/custom-management-commands/   python3 manage.py respit_launcher
import time

from django.core.management.base import BaseCommand, CommandError

class Command(BaseCommand):
    help = "Closes the specified poll for voting"

    def handle(self, *args, **options):

        for p in Video.objects.raw('SELECT * FROM video_video'):
            data_to_add = {}

            #print(p.id)
            #print(p.title)

            data_to_add['id'] = p.id
            data_to_add['title'] = p.title
            data_to_add['view_count'] = p.get_viewcount()
            data_to_add['view_count_year'] = p.get_viewcount(365)

            today = datetime.now()
            diff = today - datetime(p.date_added.year, p.date_added.month, p.date_added.day, p.date_added.hour, p.date_added.minute, p.date_added.second)
            data_to_add['date_added'] =  datetime(p.date_added.year, p.date_added.month, p.date_added.day, p.date_added.hour, p.date_added.minute, p.date_added.second)
            data_to_add['days_on_platform'] =  diff.days
            data_to_add['date_delete'] =  p.date_delete
            data_to_add['description'] =  p.description

            #Nombre de chaines
            nb_chaine = 0
            for vvc in Video.objects.raw('SELECT * FROM video_video_channel Where video_id ='+str(p.id)):
                nb_chaine = nb_chaine+1
            data_to_add['channel_count'] = nb_chaine


            #Nombre de fois en favoris
            cfav=0
            for fav in Video.objects.raw("SELECT ppone.id FROM video_video vv INNER JOIN playlist_playlistcontent pp ON vv.id = pp.video_id INNER JOIN playlist_playlist ppone ON ppone.id = pp.playlist_id WHERE ppone.name='Favorites' AND vv.id="+str(p.id)):
                cfav=cfav+1

            data_to_add['nb_fav'] = cfav

            #nb comment
            nb_comment=0
            for fav in Video.objects.raw("SELECT * FROM video_comment WHERE video_id ="+str(p.id)):
                nb_comment = nb_comment+1

            data_to_add['nb_comment'] = nb_comment

            #duration
            data_to_add['duration_video'] = time.strftime("%H:%M:%S", time.gmtime(p.duration))

            #video type
            type = ""
            for tv in Video.objects.raw("SELECT vv.id, vt.title AS title_type FROM video_video vv LEFT JOIN video_type vt ON vv.type_id = vt.id WHERE vv.id = "+str(p.id)):
                type = tv.title_type

            data_to_add['type_video'] = type

            #Video Theme
            sqltheme = "SELECT vv.id, vv.title, vt.id AS theme_id, vt.title AS theme_name FROM video_video_channel vvc INNER JOIN video_video vv ON vv.id = vvc.video_id INNER JOIN video_theme vt " + "ON vt.channel_id = vvc.id WHERE vv.id = "+str(p.id)
            theme_list = []
            for vthe in Video.objects.raw(sqltheme):
                theme_list.append(vthe.theme_name)

            data_to_add['themes_video'] = theme_list

            #Video Owner
            for ow in Video.objects.raw("SELECT v.id, au.username, au.email FROM video_video v INNER JOIN auth_user au ON v.owner_id = au.id  Where v.id =" + str(p.id)):
                data_to_add['owner_video'] = ow.username

            #Video Owner Additionnal
            additionnal_owner_list = []
            for owc in Video.objects.raw("SELECT au.id, au.username, au.email FROM video_video_additional_owners vvao LEFT JOIN auth_user au ON au.id = vvao.user_id  WHERE vvao.video_id = " + str(p.id)):
                additionnal_owner_list.append(owc.username)

            data_to_add['owner_video_additional'] = additionnal_owner_list

            #Categorie
            category_list = []
            for cat in Video.objects.raw("SELECT vc.id, vc.slug FROM video_category_video vcv INNER JOIN video_category vc ON vc.id = vcv.category_id WHERE video_id="+str(p.id)):
                category_list.append(cat.slug)

            data_to_add['category_list'] = category_list

            #laucnh the calcul model
            mod = importlib.import_module("pod.video.management.commands.respit_model."+RESPIT_MODEL)

            #Insert répis in BDD
            daysmore = mod.calcul(data_to_add)
            p.date_delete = p.date_delete + timedelta(days=daysmore)
            p.save()

            print("Add "+str(daysmore)+" days to the delete_date")
            print(p.date_delete)
            print("")