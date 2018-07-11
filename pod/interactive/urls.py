from django.conf.urls import url
from .views import edit_interactive

app_name = 'interactive'

urlpatterns = [
    url(r'^edit/(?P<slug>[\-\d\w]+)/$',
        edit_interactive,
        name='edit_interactive')
]
