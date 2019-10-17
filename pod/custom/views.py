from django.shortcuts import render
from django.http import HttpResponse
from pod.video.models import Video
import json, html
from django.db.models import Q
from pod.authentication.models import User

# Create your views here.

def index(request):
    return HttpResponse("Hello word from custom")

def update_owner(request):
    if request.method == "POST":
        print("****************", "POST REQUEST", "******************")
        post_data = json.loads(request.body.decode("utf-8"))
        response_json = change_owner(
            post_data['videos'], post_data['new_owner'])
        print("----------------->",json.dumps(response_json))
        return HttpResponse(json.dumps(response_json), content_type="application/json")
    data = get_video_essentiels_data()
    return render(request, "custom/layouts/change_video_owner/index.html", {"data": data })


def change_owner(videos, new_owner_login):
    new_owner = User.objects.get(username=new_owner_login)
    vs = []
    if not new_owner:
        return {"error": "Impossible de trouver l'utilisateur : % " % new_owner_login}
    if isinstance(videos, str):
        vs = Video.objects.all();
    else:
        # data = id-username
        for data in videos:
            id_video,owner_username = data.split("-")
            v = Video.objects.get(
                Q(pk=id_video),
                Q(owner__username=owner_username))
            vs.append(v)
    if len(vs) == 0:
        return {
            "error": "Les videos sélectionnées n'appartiennent plus à %s ou n'existent plus." % owner_username }
    for v in vs:
        v.owner = new_owner
        v.save()
    return {"success": True}
        




# return all video with only id, username and title
def get_video_essentiels_data():
    videos = Video.objects.all()
    es_data = {}
    for v in videos:
        if v.owner.username in es_data:
            es_data[v.owner.username].append(
                {
                    "id": v.pk,
                    "title": v.title,
                    "thumbnail": v.get_thumbnail_url(),
                    "url": v.get_full_url()
                }
        
            )
        else:
            es_data[v.owner.username] = []
            es_data[v.owner.username].append(
                    {
                        "id": v.pk,
                        "title": v.title,
                        "thumbnail": v.get_thumbnail_url(),
                        "url": v.get_full_url()
                    }
                    )
    return html.unescape(json.dumps(es_data, ensure_ascii=False))


        
