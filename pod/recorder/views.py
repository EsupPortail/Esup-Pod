import os

from django.shortcuts import render
from django.conf import settings
from django.urls import reverse
from django.core.exceptions import PermissionDenied
from django.shortcuts import redirect
from django.contrib.admin.views.decorators import staff_member_required
from django.views.decorators.csrf import csrf_protect
from django.utils.translation import ugettext_lazy as _

from .forms import RecordingForm
from django.contrib import messages

DEFAULT_RECORDER_PATH = getattr(
    settings, 'DEFAULT_RECORDER_PATH',
    "/home/pod/files/"
)


@csrf_protect
@staff_member_required(redirect_field_name='referrer')
def add_recording(request):
    mediapath = request.GET.get('mediapath')
    course_title = request.GET.get(
        'course_title') if request.GET.get('course_title') else ""
    course_type = request.GET.get('type')

    if not mediapath and not request.user.is_superuser:
        messages.add_message(
            request, messages.ERROR, _('Mediapath should be indicated.'))
        raise PermissionDenied

    form = RecordingForm(request, initial={
        'source_file': os.path.join(DEFAULT_RECORDER_PATH, mediapath),
        'title': course_title,
        'type': course_type})

    if request.method == 'POST':  # If the form has been submitted...
        # A form bound to the POST data
        form = RecordingForm(request, request.POST)
        if form.is_valid():  # All validation rules pass
            med = form.save(commit=False)
            if request.POST.get('user') and request.POST.get('user') != "":
                med.user = form.cleaned_data['user']
            else:
                med.user = request.user
            if request.POST.get('mediapath') and request.POST.get('mediapath') != "":
                med.mediapath = form.cleaned_data['mediapath']
            else:
                med.mediapath = mediapath
            med.save()
            message = _(
                'Your publication is saved.'
                ' Adding it to your videos will be in a few minutes.')
            messages.add_message(request, messages.INFO, message)
            return redirect(reverse('my_videos'))
        else:
            message = _('One or more errors have been found in the form.')
            messages.add_message(request, messages.ERROR, message)

    return render(request, "recorder/add_recording.html",
                  {"form": form})
