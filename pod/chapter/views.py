from django.http import HttpResponse
from django.http import HttpResponseForbidden
from django.shortcuts import render
from django.shortcuts import get_object_or_404
from django.template.loader import render_to_string
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.utils.translation import ugettext as _
from django.views.decorators.csrf import csrf_protect
from pod.video.models import Video
from pod.chapter.models import Chapter
from pod.chapter.forms import ChapterForm
from pod.chapter.forms import ChapterImportForm
from django.middleware.csrf import get_token
from django.contrib.sites.shortcuts import get_current_site

import json

ACTION = ["new", "save", "modify", "delete", "cancel", "import", "export"]


@csrf_protect
@login_required(redirect_field_name="referrer")
def video_chapter(request, slug):
    video = get_object_or_404(Video, slug=slug, sites=get_current_site(request))
    if (
        request.user != video.owner
        and not (
            request.user.is_superuser or request.user.has_perm("chapter.change_chapter")
        )
        and (request.user not in video.additional_owners.all())
    ):
        messages.add_message(request, messages.ERROR, _("You cannot chapter this video."))
        return HttpResponseForbidden(
            "Only the owner and additional owners " "can add chapter."
        )

    list_chapter = video.chapter_set.all()
    body = request.body.decode("utf-8")

    if request.method == 'POST' :
        data = json.loads(body)
        if data.get("action"):
            if data.get("action") in ACTION:
                return eval(
                    "video_chapter_{0}(request, video)".format(data.get("action"))
                )
    else:
        return render(
            request,
            "video_chapter.html",
            {"video": video, "list_chapter": list_chapter},
        )


def video_chapter_new(request, video):
    list_chapter = video.chapter_set.all()
    form_chapter = ChapterForm(initial={"video": video})
    form_import = ChapterImportForm(user=request.user, video=video)
    if request:
        return render(
            request,
            "chapter/form_chapter.html",
            {
                "form_chapter": form_chapter,
                "form_import": form_import,
                "video": video,
            },
        )
    else:
        return render(
            request,
            "video_chapter.html",
            {
                "video": video,
                "list_chapter": list_chapter,
                "form_chapter": form_chapter,
                "form_import": form_import,
            },
        )


def video_chapter_save(request, video):
    list_chapter = video.chapter_set.all()
    form_chapter = None
    body = request.body.decode("utf-8")
    data = json.loads(body)
    data = data.get("data")
    chapter_id = data.get("chapter_id")
    if chapter_id != "None" and chapter_id is not None:
        chapter = get_object_or_404(Chapter, id=chapter_id)
        form_chapter = ChapterForm(data, instance=chapter)
    else:
        form_chapter = ChapterForm(data)
    if form_chapter.is_valid():
        form_chapter.save()
        list_chapter = video.chapter_set.all()
        if request:
            csrf_token_value = get_token(request)
            some_data_to_dump = {
                "list_chapter": render_to_string(
                    "chapter/list_chapter.html",
                    {
                        "list_chapter": list_chapter,
                        "video": video,
                        "csrf_token_value": csrf_token_value,
                    },
                    request=request,
                ),
                "video-elem": render_to_string(
                    "videos/video-element.html",
                    {"video": video},
                    request=request,
                ),
            }
            data = json.dumps(some_data_to_dump)
            return HttpResponse(data, content_type="application/json")
        else:
            return render(
                request,
                "video_chapter.html",
                {"video": video, "list_chapter": list_chapter},
            )
    else:
        if request:
            csrf_token_value = get_token(request)
            some_data_to_dump = {
                "errors": "{0}".format(_("Please correct errors.")),
                "form": render_to_string(
                    "chapter/form_chapter.html",
                    {
                        "video": video,
                        "form_chapter": form_chapter,
                        "csrf_token_value": csrf_token_value,
                    },
                    request=request,
                ),
            }
            data = json.dumps(some_data_to_dump)
            return HttpResponse(data, content_type="application/json")
        else:
            return render(
                request,
                "video_chapter.html",
                {
                    "video": video,
                    "list_chapter": list_chapter,
                    "form_chapter": form_chapter,
                },
            )


def video_chapter_modify(request, video):
    list_chapter = video.chapter_set.all()
    body = request.body.decode("utf-8")
    data = json.loads(body)
    if data.get("action") and data.get("action") == "modify":
        chapter = get_object_or_404(Chapter, id=data.get("id"))
        form_chapter = ChapterForm(instance=chapter)
        if request:
            return render(
                request,
                "chapter/form_chapter.html",
                {"form_chapter": form_chapter, "video": video},
            )
        else:
            return render(
                request,
                "video_chapter.html",
                {
                    "video": video,
                    "list_chapter": list_chapter,
                    "form_chapter": form_chapter,
                },
            )


def video_chapter_delete(request, video):
    list_chapter = video.chapter_set.all()
    body = request.body.decode("utf-8")
    data = json.loads(body)

    chapter = get_object_or_404(Chapter, id=data.get("id"))
    chapter.delete()
    list_chapter = video.chapter_set.all()
    if request:
        csrf_token_value = get_token(request)
        some_data_to_dump = {
            "list_chapter": render_to_string(
                "chapter/list_chapter.html",
                {
                    "list_chapter": list_chapter,
                    "video": video,
                    "csrf_token_value": csrf_token_value,
                },
                request=request,
            ),
            "video-elem": render_to_string(
                "videos/video-element.html", {"video": video}, request=request
            ),
        }
        data = json.dumps(some_data_to_dump)
        return HttpResponse(data, content_type="application/json")
    else:
        return render(
            request,
            "video_chapter.html",
            {"video": video, "list_chapter": list_chapter},
        )


def video_chapter_cancel(request, video):
    list_chapter = video.chapter_set.all()

    return render(
        request,
        "video_chapter.html",
        {"video": video, "list_chapter": list_chapter},
    )


def video_chapter_import(request, video):
    list_chapter = video.chapter_set.all()
    body = request.body.decode("utf-8")
    data = json.loads(body)
    form_chapter = ChapterForm(initial={"video": video})
    form_import = ChapterImportForm(data, user=request.user, video=video)
    if form_import.is_valid():
        list_chapter = video.chapter_set.all()
        if request:
            csrf_token_value = get_token(request)
            some_data_to_dump = {
                "list_chapter": render_to_string(
                    "chapter/list_chapter.html",
                    {
                        "list_chapter": list_chapter,
                        "video": video,
                        "csrf_token_value": csrf_token_value,
                    },
                    request=request,
                ),
                "video-elem": render_to_string(
                    "videos/video-element.html",
                    {"video": video},
                    request=request,
                ),
            }
            data = json.dumps(some_data_to_dump)
            return HttpResponse(data, content_type="application/json")
        else:
            return render(
                request,
                "video_chapter.html",
                {"video": video, "list_chapter": list_chapter},
            )
    else:
        if request:
            some_data_to_dump = {
                "errors": "{0}".format(_("Please correct errors.")),
                "form": render_to_string(
                    "chapter/form_chapter.html",
                    {
                        "video": video,
                        "form_import": form_import,
                        "form_chapter": form_chapter,
                        "csrf_token": request.COOKIES["csrftoken"],
                    },
                ),
            }
            data = json.dumps(some_data_to_dump)
            return HttpResponse(data, content_type="application/json")
        else:
            return render(
                request,
                "video_chapter.html",
                {
                    "video": video,
                    "list_chapter": list_chapter,
                    "form_chapter": form_chapter,
                    "form_import": form_import,
                },
            )
