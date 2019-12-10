from django.shortcuts import render
from django.http import HttpResponse, HttpResponseForbidden, HttpResponseRedirect, JsonResponse
from pod.video.models import Video, Channel, ViewCount
import json, html
from pod.authentication.models import User
from django.views.decorators.csrf import csrf_protect
from django.contrib.auth.decorators import login_required
from datetime import datetime, timedelta
from django.db.models import Sum
from django.views.decorators.clickjacking import xframe_options_sameorigin

TODAY = datetime.now()

def index(request):
    return HttpResponse("Hello word from custom")

#@xframe_options_sameorigin
#def mentions_legales(request):
#    return render(request, "custom/layouts/mentions-legales.html", {})

def total_view(v_id):
    seven_days_ago = TODAY - timedelta(days=7)
    total_view = []
    # Ajout nb de vue total aujourd'hui
    total_view.append(ViewCount.objects.filter(
        video_id=v_id,
        date__year=TODAY.year,
        date__month=TODAY.month,
        date__day=TODAY.day).aggregate(
            Sum('count'))['count__sum']
        )
    # Ajout nb de vue total cette semaine
    total_view.append(ViewCount.objects.filter(
        video_id=v_id,
        date__lte=TODAY,
        date__gte=seven_days_ago).aggregate(
            Sum('count'))['count__sum']
        )
    # Ajout nb de vue total ce mois ci
    total_view.append(ViewCount.objects.filter(
        video_id=v_id,
        date__year=TODAY.year,
        date__month=TODAY.month).aggregate(
            Sum('count'))['count__sum']
        )
    # Ajout nb de vue total cette année
    total_view.append(ViewCount.objects.all().filter(
        date__year=TODAY.year,
        video_id=v_id).aggregate(
            Sum('count'))['count__sum']
        )
    # Ajout nb de vue depuis la création de la vidéo
    total_view.append(ViewCount.objects.filter(
        video_id=v_id).aggregate(
            Sum('count'))['count__sum']
        )
    # replace None by 0
    return [ nb if nb else 0 for nb in total_view  ]

# request, data, column, ASC=True
def ordering_data_by(data, col='title', ASC=True):
    # ordering data
    return sorted(data, key=lambda v: v[col], reverse=ASC)

# Retourne une ou plusieurs videos
# selon le type du slug donné (video ou channel)
def get_videos(p_slug, target):
    videos = []
    print("------------ target -------------")
    print(target)
    if target.lower() == "video":
        videos.append(
                Video.objects.filter(
                    slug__istartwith=p_slug).first())
    if target.lower() == "channel" and not videos:
        channel = Channel.objects.filter(
                slug__istartswith=slug).first()
        if channel:
            # Recupere les vidéos associées à cette chaîne
            videos = Video.objects.filter(channel=channel)
    return videos

def order(request):
    if request.is_ajax() and request.method == "POST":
        (_data, _col, _dir) = (
                request.POST.getlist('col', 'title'),
                request.POST.getlist('asc', True),
                request.POST.getlist('data', []))
        print("**********************************")
        print(_col, _dir, _data)
        print("----------------------------------")
        data = ordering_data_by(
                request.getlist())
        return JsonResponse({"data":data})

def stats_view(request, slug):
    # Slug peut-etre une video ou une chaîne
    # Pour definir le on a une variable from en post
    if request.method == "GET":
        target = request.GET.getlist('from', None)
        print("*************", target, "*****************")
        videos = get_videos(slug, target)
        if not videos:
            return HttpResponseForbidden(
                    "La chaine ou la video suivante n' existe pas : %s" % slug)
        data = []
        for v in videos:
            v_data = {}
            v_data['title'] = v.title
            (v_data['day'],
                    v_data['week'],
                    v_data['month'],
                    v_data['year'],
                    v_data['since_created']) = total_view(v.id)
            data.append(v_data)
        data = ordering_data(data)
        return render(
                request,
                "custom/layouts/statistique-video.html",
                {"data" :data, "channel_slug": slug, "channel_title": channel.title})


@csrf_protect
@login_required(redirect_field_name="referrer")
def update_owner(request):
    if request.method == "POST":
        post_data = json.loads(request.body.decode("utf-8"))
        response_json = change_owner(
            post_data['videos'],
            post_data['old_owner'],
            post_data['new_owner'])
        if 'success' in response_json:
            return HttpResponse(
                    json.dumps(response_json),
                    content_type="application/json")
        return HttpResponseForbidden(response_json['error'])
    # if it's GET request
    return HttpResponseRedirect('/')
    # data = get_video_essentiels_data()
    # return render(
    #        request,
    #        "custom/layouts/change_video_owner/index.html",
    #        {"data": data })


def change_owner(videos, old_owner, new_owner_login):
    new_owner = User.objects.filter(username=new_owner_login).first()
    if not new_owner:
        return {
                "error": "Impossible de trouver le nouveau propriétaire : {%s}"\
                        % new_owner_login}
    vs = []
    if isinstance(videos, str):
        vs = Video.objects.filter(owner__username__startswith=old_owner);
    else:
        # expected :
        # data = id-username
        # videos = [ "id-username", "id-username", ...]
        for data in videos:
            id_owner,video_title = data.split("|-|")
            id_video,owner_username = id_owner.split('-')
            v = Video.objects.filter(
                    pk=id_video,
                    owner__username=owner_username).first()
            if not v:
                return {
                        "error": "Impossible de faire le changement.\n La \
                                vidéo '{%s}' n'existe pas ou a été supprimée.\
                        " % video_title }
            vs.append(v)
    if len(vs) == 0:
        return {
            "error": "Les videos sélectionnées n'appartiennent \
                    plus à {%s} ou n'existent plus." % owner_username }
    for v in vs:
        v.owner = new_owner
        v.save()
    return {"success": True}
        
# return all videos with id, title thumbnail and url data
def get_video_essentiels_data():
    videos = Video.objects.all()
    users = User.objects.all();
    es_data = {}
    for user in users:
        es_data[user.username]  = []
        vs = Video.objects.filter(owner=user)
        if not vs:
            es_data[user.username] = { "full_name": "%s %s" % (
                user.last_name,
                user.first_name
                )} 
            continue
        for v in vs:
            es_data[user.username].append({
                    "id": v.pk,
                    "full_name": "%s %s" % (
                        v.owner.last_name,
                        v.owner.first_name),
                    "title": v.title,
                    "thumbnail": v.get_thumbnail_url(),
                    "url": v.get_full_url()
                    })
    print(html.unescape(json.dumps(es_data, ensure_ascii=False)))

    ###
    #for v in videos:
    #    if v.owner.username in es_data:
    #        es_data[v.owner.username].append(
    #            {
    #                "id": v.pk,
    #                "full_name": "%s %s" % (
    #                    v.owner.last_name,
    #                    v.owner.first_name),
    #                "title": v.title,
    #                "thumbnail": v.get_thumbnail_url(),
    #                "url": v.get_full_url()
    #            }
    #    
    #        )
    #    else:
    #        es_data[v.owner.username] = []
    #        es_data[v.owner.username].append(
    #                {
    #                    "id": v.pk,
    #                    "full_name": "%s %s" % (
    #                        v.owner.last_name,
    #                        v.owner.first_name),
    #                    "title": v.title,
    #                    "thumbnail": v.get_thumbnail_url(),
    #                    "url": v.get_full_url()
    #                }
    #                )
    ###
    return html.unescape(json.dumps(es_data, ensure_ascii=False))


        
