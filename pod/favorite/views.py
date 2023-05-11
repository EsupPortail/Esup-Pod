from django.contrib.sites.shortcuts import get_current_site
from django.core.paginator import EmptyPage, PageNotAnInteger, Paginator
from django.db import transaction
from django.http import Http404, HttpResponseBadRequest
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.csrf import csrf_protect
from django.contrib.auth.decorators import login_required
from pod.favorite.models import Favorite

from pod.video.models import Video
from pod.video.views import CURSUS_CODES, get_owners_has_instances

from .utils import user_add_or_remove_favorite_video
from .utils import get_all_favorite_videos_for_user
from .utils import sort_videos_list

import json


@csrf_protect
def favorite_button_in_video_info(request):
    if request.method == "POST":
        video = get_object_or_404(
            Video,
            pk=request.POST.get("video"),
            sites=get_current_site(request)
        )
        user_add_or_remove_favorite_video(request.user, video)
        return redirect(request.META["HTTP_REFERER"])
    else:
        raise Http404()


@login_required(redirect_field_name="referrer")
def favorite_list(request):
    """Render the main list of favorite videos."""
    videos_list = sort_videos_list(
        request,
        get_all_favorite_videos_for_user(request.user)
    )
    count_videos = len(videos_list)

    page = request.GET.get("page", 1)
    full_path = ""
    if page:
        full_path = (
            request.get_full_path()
            .replace("?page=%s" % page, "")
            .replace("&page=%s" % page, "")
        )

    paginator = Paginator(videos_list, 12)
    try:
        videos = paginator.page(page)
    except PageNotAnInteger:
        videos = paginator.page(1)
    except EmptyPage:
        videos = paginator.page(paginator.num_pages)

    ownersInstances = get_owners_has_instances(request.GET.getlist("owner"))

    if request.is_ajax():
        return render(
            request,
            "favorite/favorite_videos_list.html",
            {"videos": videos, "full_path": full_path, "count_videos": count_videos},
        )

    return render(
        request,
        "favorite/favorite_videos.html",
        {
            "videos": videos,
            "count_videos": count_videos,
            "types": request.GET.getlist("type"),
            "owners": request.GET.getlist("owner"),
            "disciplines": request.GET.getlist("discipline"),
            "tags_slug": request.GET.getlist("tag"),
            "cursus_selected": request.GET.getlist("cursus"),
            "full_path": full_path,
            "ownersInstances": ownersInstances,
            "cursus_list": CURSUS_CODES,
        },
    )


@csrf_protect
def favorites_save_reorganisation(request):
    if request.method == "POST":
        json_data = request.POST.get("json-data")
        try:
            dict_data = json.loads(json_data)
        except json.JSONDecodeError:
            return HttpResponseBadRequest("JSON au mauvais format")
        with transaction.atomic():
            for videos_tuple in dict_data.values():
                fav_video_1 = Favorite.objects.filter(
                    owner_id=request.user.id,
                    video_id=Video.objects.only('id').get(slug=videos_tuple[0]).id
                )
                fav_video_2 = Favorite.objects.filter(
                    owner_id=request.user.id,
                    video_id=Video.objects.only('id').get(slug=videos_tuple[1]).id
                )
                video_1_rank = fav_video_1[0].rank
                video_2_rank = fav_video_2[0].rank
                fav_video_1.update(rank=video_2_rank)
                fav_video_2.update(rank=video_1_rank)

        return redirect(request.META["HTTP_REFERER"])
    else:
        raise Http404()
