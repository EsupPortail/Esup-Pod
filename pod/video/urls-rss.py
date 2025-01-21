from django.conf.urls import url
from .feeds import RssSiteVideosFeed, RssSiteAudiosFeed

app_name = "rss-video"

urlpatterns = [
    url(r"^-video/$", RssSiteVideosFeed(), name="rss-video"),
    url(r"^-audio/$", RssSiteAudiosFeed(), name="rss-audio"),
    url(
        r"^-video/(?P<slug_c>[\-\d\w]+)/$",
        RssSiteVideosFeed(),
        name="rss-video",
    ),
    url(
        r"^-audio/(?P<slug_c>[\-\d\w]+)/$",
        RssSiteAudiosFeed(),
        name="rss-audio",
    ),
    url(
        r"^-video/(?P<slug_c>[\-\d\w]+)/(?P<slug_t>[\-\d\w]+)/$",
        RssSiteVideosFeed(),
        name="rss-video",
    ),
    url(
        r"^-audio/(?P<slug_c>[\-\d\w]+)/(?P<slug_t>[\-\d\w]+)/$",
        RssSiteAudiosFeed(),
        name="rss-audio",
    ),
]
