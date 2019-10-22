from django import template
from pod.authentication.models import User
from pod.custom.views import get_video_essentiels_data

register = template.Library()

def data():
    return get_video_essentiels_data
