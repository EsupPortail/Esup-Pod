from django.contrib import admin
from pod.video.models import Video
from pod.video.models import Channel
from pod.video.models import Theme
from pod.video.models import Type
from pod.video.models import Discipline

# Register your models here.
admin.site.register(Video)
admin.site.register(Channel)
admin.site.register(Theme)
admin.site.register(Type)
admin.site.register(Discipline)
