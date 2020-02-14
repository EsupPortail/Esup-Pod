from django.views.generic.base import TemplateView
from lti_provider.mixins import LTIAuthMixin
from auth_mixins import LoginRequiredMixin
from django.urls import reverse
from django.contrib import messages
from django.utils.translation import ugettext_lazy as _

from django.utils.decorators import method_decorator
# from django.views.decorators.csrf import ensure_csrf_cookie
# from django.views.decorators.csrf import csrf_protect, csrf_exempt
from django.views.decorators.csrf import csrf_exempt

from pod.video.models import Video

# Create your views here.

@method_decorator([csrf_exempt], name='dispatch')
class LTIAssignmentView(LTIAuthMixin, LoginRequiredMixin, TemplateView):

    template_name = 'lti_provider/assignment.html'

    def get_context_data(self, **kwargs):
        # print(kwargs)
        # print(self.request, self.request.get_full_url())
        activity = kwargs.get("activity")
        url = ""
        if activity == 'addvideo':
            # "http://localhost:8000/video_edit/?is_iframe=true"
            url = reverse('video_edit')
            url += "?is_iframe=true"
            # url = "/video_edit/?is_iframe=true"
        if activity == 'getvideo':
            if self.request.session.get("custom_video"):
                try:
                    video = Video.objects.get(
                        id=self.request.session.get("custom_video"))
                    # "http://localhost:8000/video_edit/?is_iframe=true"
                    url = reverse('video', args=(video.slug,))
                    url += "?is_iframe=true"
                    # url = "http:" + video.get_full_url() + "?is_iframe=true"
                except Exception:
                    messages.add_message(
                        self.request,
                        messages.ERROR,
                        _('The video id is not valid.'))
        return {
            'iframe_url': url,
            'is_student': self.lti.lis_result_sourcedid(self.request),
            'course_title': self.lti.course_title(self.request),
            'number': 1
        }
