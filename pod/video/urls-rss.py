"""Esup-Pod urls-rss."""

from django.urls import path, re_path
from .feeds import RssSiteVideosFeed, RssSiteAudiosFeed

app_name = "rss-video"

urlpatterns = [
    path("-video/", RssSiteVideosFeed(), name="rss-video"),
    path("-audio/", RssSiteAudiosFeed(), name="rss-audio"),
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
