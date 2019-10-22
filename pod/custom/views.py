from django.shortcuts import render
from django.http import HttpResponse, HttpResponseForbidden
from pod.video.models import Video
import json, html
from pod.authentication.models import User
from django.views.decorators.csrf import csrf_protect
from django.contrib.auth.decorators import login_required


def index(request):
    return HttpResponse("Hello word from custom")


@csrf_protect
def update_owner(request):
    print("************** HERE YOU ARE ********************")
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
    data = get_video_essentiels_data()
    return render(
            request,
            "admin/custom/admin/change_video_owner.html",
            {"data": data })


def change_owner(videos, old_owner, new_owner_login):
    new_owner = User.objects.filter(username=new_owner_login).first()
    print(new_owner, "++++++++++++++++++++++++++++++++++++++")
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


        
