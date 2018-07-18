from django.conf.urls import url
from .views import edit_interactive, group_interactive, video_interactive

app_name = 'interactive'

urlpatterns = [
    url(r'^edit/(?P<slug>[\-\d\w]+)/$',
        edit_interactive,
        name='edit_interactive'),
    url(r'^group/(?P<slug>[\-\d\w]+)/$',
        group_interactive,
        name='group_interactive'),
    url(r'^video/(?P<slug>[\-\d\w]+)/$',
        video_interactive,
        name='video_interactive'),
    url(r'^video/(?P<slug>[\-\d\w]+)/(?P<slug_private>[\-\d\w]+)/$',
        video_interactive,
        name='video_interactive_private')
]
