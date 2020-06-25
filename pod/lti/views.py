from django.views.generic.base import TemplateView
from lti_provider.mixins import LTIAuthMixin
from django.contrib.auth.mixins import LoginRequiredMixin

from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import render

from django.urls import reverse
from django.contrib import messages
from django.utils.translation import ugettext_lazy as _

from pod.video.models import Video


@method_decorator([csrf_exempt], name='dispatch')
class LTIAssignmentAddVideoView(
        LTIAuthMixin, LoginRequiredMixin, TemplateView):

    redirect_field_name = 'referrer'
    template_name = 'lti_provider/assignment.html'

    def get_context_data(self, **kwargs):
        context = super(LTIAssignmentAddVideoView,
                        self).get_context_data(**kwargs)
        url = reverse('video_edit')
        url += "?is_iframe=true"
        context['iframe_url'] = url
        context['is_student'] = self.lti.lis_result_sourcedid(self.request),
        context['course_title'] = self.lti.course_title(self.request),
        context['number'] = 1
        return context

    def post(self, request, *args, **kwargs):
        return render(
            request, self.template_name, self.get_context_data(**kwargs))


@method_decorator([csrf_exempt], name='dispatch')
class LTIAssignmentGetVideoView(
        LTIAuthMixin, LoginRequiredMixin, TemplateView):

    redirect_field_name = 'referrer'
    template_name = 'lti_provider/assignment.html'

    def get_context_data(self, **kwargs):
        context = super(LTIAssignmentGetVideoView,
                        self).get_context_data(**kwargs)
        if self.request.session.get("custom_video"):
            try:
                video = Video.objects.get(
                    id=self.request.session.get("custom_video"))
                url = reverse('video', args=(video.slug,))
                url += "?is_iframe=true"
                context['iframe_url'] = url
            except Exception:
                messages.add_message(
                    self.request,
                    messages.ERROR,
                    _('The video id is not valid.'))
        context['is_student'] = self.lti.lis_result_sourcedid(
            self.request),
        context['course_title'] = self.lti.course_title(self.request),
        context['number'] = 1
        return context

    def post(self, request, *args, **kwargs):
        return render(
            request, self.template_name, self.get_context_data(**kwargs))
