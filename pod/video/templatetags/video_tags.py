from django.conf import settings as django_settings
from django import template
from django.utils.text import capfirst
from django.urls import reverse
from django.db.models import Q
from django.contrib.sites.shortcuts import get_current_site
from django.template import TemplateSyntaxError
from django.apps.registry import apps
from django.utils.translation import ugettext_lazy as _

from tagging.templatetags.tagging_tags import TagsForModelNode, TagCloudForModelNode
from tagging.models import Tag
from tagging.utils import LINEAR
from tagging.utils import LOGARITHMIC

from ..forms import VideoVersionForm
from ..context_processors import get_available_videos
from pod.video_encode_transcript.utils import check_file
from django.contrib.auth.models import User
from pod.video.models import Video

import importlib
import os

register = template.Library()

HOMEPAGE_SHOWS_PASSWORDED = getattr(django_settings, "HOMEPAGE_SHOWS_PASSWORDED", True)
HOMEPAGE_SHOWS_RESTRICTED = getattr(django_settings, "HOMEPAGE_SHOWS_RESTRICTED", True)
HOMEPAGE_NB_VIDEOS = getattr(django_settings, "HOMEPAGE_NB_VIDEOS", 12)
HOMEPAGE_VIEW_VIDEOS_FROM_NON_VISIBLE_CHANNELS = getattr(
    django_settings, "HOMEPAGE_VIEW_VIDEOS_FROM_NON_VISIBLE_CHANNELS", False
)


@register.simple_tag(name="get_marker_time_for_user")
def get_marker_time_for_user(video: Video, user: User):
    """Tag to get the marker time of the video for the authenticated user."""
    return video.get_marker_time_for_user(user)


@register.simple_tag(name="get_percent_marker_for_user")
def get_percent_marker_for_user(video: Video, user: User):
    """Tag to get the percent time of the video viewed by the authenticated user."""
    if video.duration and video.duration != 0:
        return int((video.get_marker_time_for_user(user) / video.duration) * 100)
    else:
        return 0


@register.filter(name="file_exists")
def file_exists(filepath):
    return check_file(filepath.path)


@register.filter(name="file_date_created")
def file_date_created(filepath):
    if check_file(filepath.path):
        return os.path.getctime(filepath.path)


@register.filter(name="file_date_modified")
def file_date_modified(filepath):
    if check_file(filepath.path):
        return os.path.getmtime(filepath.path)


@register.simple_tag
def get_app_link(video, app):
    mod = importlib.import_module("pod.%s.models" % app)
    if hasattr(mod, capfirst(app)):
        video_app = eval(
            "mod.%s.objects.filter(video__id=%s).all()" % (capfirst(app), video.id)
        )
        if (
            app == "interactive"
            and video_app.first() is not None
            and video_app.first().is_interactive() is False
        ):
            video_app = False
        if video_app:
            url = reverse(
                "%(app)s:video_%(app)s" % {"app": app},
                kwargs={"slug": video.slug},
            )
            return (
                '<a href="%(url)s" title="%(app)s" '
                'class="dropdown-item" target="_blank">%(link)s</a>'
            ) % {"app": app, "url": url, "link": mod.__NAME__}
    return ""


@register.simple_tag
def get_version_form(video):
    form = VideoVersionForm()
    return form


@register.simple_tag(takes_context=True)
def get_last_videos(context):
    request = context["request"]
    videos = get_available_videos().filter(
        sites=get_current_site(request),
    )

    if not HOMEPAGE_VIEW_VIDEOS_FROM_NON_VISIBLE_CHANNELS:
        videos = videos.exclude(channel__visible=0)

    if not HOMEPAGE_SHOWS_PASSWORDED:
        videos = videos.filter(Q(password="") | Q(password__isnull=True))
    if not HOMEPAGE_SHOWS_RESTRICTED:
        videos = videos.filter(is_restricted=False)
    videos = videos.defer("video", "slug", "owner", "additional_owners", "description")
    count = 0
    recent_vids = []
    for vid in videos:
        if vid.encoded:
            recent_vids.append(vid)
            count = count + 1
        if count >= HOMEPAGE_NB_VIDEOS:
            break

    return recent_vids


@register.simple_tag(name="get_video_infos")
def get_video_infos(video):
    """
    Get videos infos (password, draft and chaptered) to display in list mode.

    Args:
        video (:class:`pod.video.models.Video`): Video object instance.

    Returns:
        Return composite object of video's infos to be accessible in template
    """
    is_password_protected = video.password or video.is_restricted
    is_chaptered = video.chapter_set.all().count() > 0
    return {
        "password": {
            "status": is_password_protected,
            "translation": _("This content is password protected.")
            if is_password_protected
            else _("This content is not password protected."),
        },
        "draft": {
            "status": video.is_draft,
            "translation": _("This content is in draft.")
            if video.is_draft
            else _("This content is public."),
        },
        "chaptered": {
            "status": is_chaptered,
            "translation": _("This content is chaptered.")
            if is_chaptered
            else _("This content is not chaptered."),
        },
    }


class getTagsForModelNode(TagsForModelNode):
    def __init__(self, model, context_var, counts):
        super(getTagsForModelNode, self).__init__(model, context_var, counts)

    def render(self, context):
        model = apps.get_model(*self.model.split("."))
        if model is None:
            raise TemplateSyntaxError(
                _("tags_for_model tag was given an invalid model: %s") % self.model
            )
        request = context["request"]
        context[self.context_var] = Tag.objects.usage_for_model(
            model,
            counts=self.counts,
            filters=dict(is_draft=False, sites=get_current_site(request)),
        )
        return ""


def do_tags_for_model(parser, token):
    """
    Retrieves a list of ``Tag`` objects associated with a given model
    and stores them in a context variable.

    Usage::

       {% tags_for_model [model] as [varname] %}

    The model is specified in ``[appname].[modelname]`` format.

    Extended usage::

       {% tags_for_model [model] as [varname] with counts %}

    If specified - by providing extra ``with counts`` arguments - adds
    a ``count`` attribute to each tag containing the number of
    instances of the given model which have been tagged with it.

    Examples::

       {% tags_for_model products.Widget as widget_tags %}
       {% tags_for_model products.Widget as widget_tags with counts %}

    """
    bits = token.contents.split()
    len_bits = len(bits)
    if len_bits not in (4, 6):
        raise TemplateSyntaxError(
            _("%s tag requires either three or five arguments") % bits[0]
        )
    if bits[2] != "as":
        raise TemplateSyntaxError(_("second argument to %s tag must be 'as'") % bits[0])
    if len_bits == 6:
        if bits[4] != "with":
            raise TemplateSyntaxError(
                _("if given, fourth argument to %s tag must be 'with'") % bits[0]
            )
        if bits[5] != "counts":
            raise TemplateSyntaxError(
                _("if given, fifth argument to %s tag must be 'counts'") % bits[0]
            )
    if len_bits == 4:
        return getTagsForModelNode(bits[1], bits[3], counts=False)
    else:
        return getTagsForModelNode(bits[1], bits[3], counts=True)


def do_tag_cloud_for_model(parser, token):
    """
    Retrieves a list of ``Tag`` objects for a given model, with tag
    cloud attributes set, and stores them in a context variable.

    Usage::

       {% tag_cloud_for_model [model] as [varname] %}

    The model is specified in ``[appname].[modelname]`` format.

    Extended usage::

       {% tag_cloud_for_model [model] as [varname] with [options] %}

    Extra options can be provided after an optional ``with`` argument,
    with each option being specified in ``[name]=[value]`` format. Valid
    extra options are:

       ``steps``
          Integer. Defines the range of font sizes.

       ``min_count``
          Integer. Defines the minimum number of times a tag must have
          been used to appear in the cloud.

       ``distribution``
          One of ``linear`` or ``log``. Defines the font-size
          distribution algorithm to use when generating the tag cloud.

    Examples::

       {% tag_cloud_for_model products.Widget as widget_tags %}
       {% tag_cloud_for_model products.Widget as widget_tags
                   with steps=9 min_count=3 distribution=log %}

    """
    bits = token.contents.split()
    len_bits = len(bits)
    if len_bits != 4 and len_bits not in range(6, 9):
        raise TemplateSyntaxError(
            _("%s tag requires either three or between five and seven arguments")
            % bits[0]
        )
    if bits[2] != "as":
        raise TemplateSyntaxError(_("second argument to %s tag must be 'as'") % bits[0])
    kwargs = {}
    if len_bits > 5:
        if bits[4] != "with":
            raise TemplateSyntaxError(
                _("if given, fourth argument to %s tag must be 'with'") % bits[0]
            )
        kwargs = get_kwargs_for_cloud(len_bits, bits)
    return TagCloudForModelNode(bits[1], bits[3], **kwargs)


def get_kwargs_for_cloud(len_bits, bits):
    kwargs = {}
    for i in range(5, len_bits):
        try:
            name, value = bits[i].split("=")
            if name in ["steps", "min_count", "distribution"]:
                kwargs = update_kwargs_from_bits(kwargs, name, value, bits)
            else:
                raise TemplateSyntaxError(
                    _("%(tag)s tag was given an invalid option: '%(option)s'")
                    % {
                        "tag": bits[0],
                        "option": name,
                    }
                )
        except ValueError:
            raise TemplateSyntaxError(
                _("%(tag)s tag was given a badly formatted option: '%(option)s'")
                % {
                    "tag": bits[0],
                    "option": bits[i],
                }
            )
    filters = dict(is_draft=False, sites=get_current_site(None))
    kwargs["filters"] = filters
    return kwargs


def update_kwargs_from_bits(kwargs, name, value, bits):
    if name == "steps" or name == "min_count":
        try:
            kwargs[str(name)] = int(value)
        except ValueError:
            raise TemplateSyntaxError(
                _(
                    "%(tag)s tag's '%(option)s' option was not "
                    "a valid integer: '%(value)s'"
                )
                % {
                    "tag": bits[0],
                    "option": name,
                    "value": value,
                }
            )
    if name == "distribution":
        if value in ["linear", "log"]:
            kwargs[str(name)] = {"linear": LINEAR, "log": LOGARITHMIC}[value]
        else:
            raise TemplateSyntaxError(
                _(
                    "%(tag)s tag's '%(option)s' option was not "
                    "a valid choice: '%(value)s'"
                )
                % {
                    "tag": bits[0],
                    "option": name,
                    "value": value,
                }
            )
    return kwargs


register.tag("tags_for_model", do_tags_for_model)
register.tag("tag_cloud_for_model", do_tag_cloud_for_model)
