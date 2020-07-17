from django.shortcuts import render
from django.http import HttpResponse, HttpResponseForbidden, HttpResponseRedirect, JsonResponse
from pod.video.models import Video, Theme, Channel, ViewCount
import json, html
from pod.authentication.models import User
from django.views.decorators.csrf import csrf_protect
from django.contrib.auth.decorators import login_required
from datetime import datetime, timedelta
from dateutil.parser import parse
from django.db.models import Sum

TODAY = datetime.now()

def index(request):
    return HttpResponse("Hello word from custom")


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
    # if it's GET request redirect to the homepage
    return HttpResponseRedirect('/')

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
        # data = id|-|video_title
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
    return html.unescape(json.dumps(es_data, ensure_ascii=False))
