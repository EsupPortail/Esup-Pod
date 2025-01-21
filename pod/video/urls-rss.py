from django.urls import re_path
from .feeds import RssSiteVideosFeed, RssSiteAudiosFeed

app_name = "rss-video"

urlpatterns = [
    re_path(r"^-video/$", RssSiteVideosFeed(), name="rss-video"),
    re_path(r"^-audio/$", RssSiteAudiosFeed(), name="rss-audio"),
    re_path(
        r"^-video/(?P<slug_c>[\-\d\w]+)/$",
        RssSiteVideosFeed(),
        name="rss-video",
    ),
    re_path(
        r"^-audio/(?P<slug_c>[\-\d\w]+)/$",
        RssSiteAudiosFeed(),
        name="rss-audio",
    ),
    re_path(
        r"^-video/(?P<slug_c>[\-\d\w]+)/(?P<slug_t>[\-\d\w]+)/$",
        RssSiteVideosFeed(),
        name="rss-video",
    ),
    re_path(
        r"^-audio/(?P<slug_c>[\-\d\w]+)/(?P<slug_t>[\-\d\w]+)/$",
        RssSiteAudiosFeed(),
        name="rss-audio",
    ),
]
