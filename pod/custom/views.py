import os
import re
import shutil
import concurrent.futures as futures

from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_protect
from django.contrib.auth.decorators import login_required
from django.db.models import Q, Value as V
from django.db.models.functions import Concat

from pod.authentication.models import User
from pod.video.models import Video  


def index(request):
    return HttpResponse("Hello word from custom")

def move_video_file(video, new_owner):
    # overview and encoding video folder name
    encod_folder_pattern = "%04d" % video.id + "/?"
    old_dest = os.path.join(
            os.path.dirname(video.video.path),
            "%04d" % video.id)
    new_dest = re.sub(
        r"\w{64}",
        new_owner.owner.hashkey,
        old_dest
    )
    
    # move encoding and overview folder
    if not os.path.exists(new_dest) and os.path.exists(old_dest):
        new_dest = re.sub(encod_folder_pattern, "", new_dest)
        if not os.path.exists(new_dest):
            os.makedirs(new_dest)
        shutil.move(old_dest, new_dest)
    
    # move video path
    video_file_pattern = r"[\w-]+\.\w+"
    old_video_path = video.video.path
    new_video_path = re.sub(
        re.search(r"\w{10,}", video.video.path).group(),
        new_owner.owner.hashkey,
        old_video_path
    )
    video.video.name = new_video_path.split("media/")[1]
    if not os.path.exists(new_video_path) and os.path.exists(old_video_path):
        new_video_path = re.sub(video_file_pattern, "", new_video_path)
        shutil.move(old_video_path, new_video_path)
    video.save()

@csrf_protect
@login_required(redirect_field_name="referrer")
def update_video_owner(request, user_id):
    if request.method == "POST":
        post_data = {**request.POST}

        videos = post_data.get("videos", [])
        owner_id = post_data.get("owner", [0,])[0]
        owner_id = int(owner_id) if owner_id.isnumeric() else 0

        response = {
            "success": True,
            "detail": "Update successfully"
        }
        if 0 in (owner_id, len(videos)):
            return JsonResponse({
                "success": False,
                "detail": "Bad request: Please one or more fields are invalid"},
                safe=False)

        videos = videos[0].split(',')

        old_owner = User.objects.filter(pk=user_id).first()
        new_owner = User.objects.filter(pk=owner_id).first()

        if None in (old_owner, new_owner):
            return JsonResponse({
                "success": False,
                "detail": "New owner or Old owner does not exist"
            }, safe=False)

        def update_owner(video_id):
            nonlocal old_owner, new_owner
            video_id = int(video_id) if video_id.isnumeric else None

            if video_id is None:
                return False

            video = Video.objects.filter(pk=video_id).first()
            if video is None:
                return False
            video.owner = new_owner
            video.save()
            move_video_file(video, new_owner)

            return True

        one_or_more_not_updated = False
        with futures.ThreadPoolExecutor() as executor:
            for v in videos:
                res = executor.submit(
                    update_owner,
                    v).result()
                if res is False:
                    one_or_more_not_updated = False

        if one_or_more_not_updated:
            return JsonResponse(
                {
                    **response,
                    "detail": "One or more videos not updated"
                }, safe=False)

        return JsonResponse(response, safe=False)

    return JsonResponse({
        **response,
        "detail": "Method not allowed: Please use post method"},
        safe=False)


def get_owners(request):
    limit = int(request.GET.get("limit", 12))
    offset = int(request.GET.get("offset", 0))
    search = request.GET.get("q", "")
    users = list(User.objects.annotate(
            full_name=Concat("first_name", V(" "), "last_name")
        ).filter(
        Q(first_name__icontains=search) |
        Q(last_name__icontains=search) |
        Q(full_name__icontains=search)
    ).values(
        "id",
        "first_name",
        "last_name",
        ))[offset:limit]
    return JsonResponse(users, safe=False)

def get_videos(request, user_id):
    limit = int(request.GET.get("limit", 12))
    offset = int(request.GET.get("offset", 0))
    title = request.GET.get("title", None)
    videos = Video.objects.filter(owner__id=user_id).order_by("id")

    if not title is None:
        videos = videos.filter(
            Q(title__icontains=title) |
            Q(title_fr__icontains=title) |
            Q(title_en__icontains=title) |
            Q(title_nl__icontains=title)
        )

    count = videos.count()
    results = list(
        map(lambda v: {
            "id": v.id,
            "title": v.title,
            "thumbnail": v.get_thumbnail_url()},
            videos[offset:limit+offset]
        )
    )
    next_url = None
    previous_url = None

    if offset + limit < count and limit <= count:
        next_url = "/custom/manage/videos/{}/?limit={}&offset={}".format(
            user_id, limit, limit + offset)
    if offset - limit >= 0 and limit <= count:
        previous_url = "/custom/manage/videos/{}/?limit={}&offset={}".format(
            user_id, limit, offset - limit)

    response = {
        "count": count,
        "next": next_url,
        "previous": previous_url,
        "results": results
    }
    return JsonResponse(response, safe=False)
