from django.contrib.sites.shortcuts import get_current_site
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.views.decorators.csrf import csrf_protect

from pod.video.models import Video

from .utils import user_add_or_remove_favorite_video


@csrf_protect
def favorite_button_in_video_info(request):
    if request.method == "POST":
        video = get_object_or_404(
            Video,
            pk=request.POST.get("video"),
            sites=get_current_site(request)
        )
        user_add_or_remove_favorite_video(request.user, video)
        return redirect(reverse("video:video", args=[video.slug]))
        # return render(
        #     request,
        #     "videos/video.html",
        #     {"video": video},
        # )
    else:
        raise Http404()
