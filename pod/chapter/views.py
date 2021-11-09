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
        messages.add_message(
            request, messages.ERROR, _(u"You cannot chapter this video.")
        )
        return HttpResponseForbidden(
            u"Only the owner and additional owners " "can add chapter."
        )

    list_chapter = video.chapter_set.all()

    if request.POST and request.POST.get("action"):
        if request.POST["action"] in ACTION:
            return eval(
                "video_chapter_{0}(request, video)".format(request.POST["action"])
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
    if request.is_ajax():
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
    if request.POST.get("chapter_id") != "None":
        chapter = get_object_or_404(Chapter, id=request.POST["chapter_id"])
        form_chapter = ChapterForm(request.POST, instance=chapter)
    else:
        form_chapter = ChapterForm(request.POST)
    if form_chapter.is_valid():
        form_chapter.save()
        list_chapter = video.chapter_set.all()
        if request.is_ajax():
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
        if request.is_ajax():
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

    if request.POST.get("action") and request.POST["action"] == "modify":
        chapter = get_object_or_404(Chapter, id=request.POST["id"])
        form_chapter = ChapterForm(instance=chapter)
        if request.is_ajax():
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

    chapter = get_object_or_404(Chapter, id=request.POST["id"])
    chapter.delete()
    list_chapter = video.chapter_set.all()
    if request.is_ajax():
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

    form_chapter = ChapterForm(initial={"video": video})
    form_import = ChapterImportForm(request.POST, user=request.user, video=video)
    if form_import.is_valid():
        list_chapter = video.chapter_set.all()
        if request.is_ajax():
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
        if request.is_ajax():
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
