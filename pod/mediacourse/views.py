# -*- coding: utf-8 -*-
from __future__ import unicode_literals
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
import hashlib
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from datetime import datetime, date
from django.utils import formats
from django.core.mail import EmailMultiAlternatives
from pod.main.context_processors import TEMPLATE_VISIBLE_SETTINGS
from django.contrib.auth.models import User
from .models import Recorder, Job
from django.core.exceptions import ObjectDoesNotExist
import urllib.parse

USE_CAS = getattr(settings, 'USE_CAS', False)

DEFAULT_MEDIACOURSE_RECORDER_PATH = getattr(
    settings, 'DEFAULT_MEDIACOURSE_RECORDER_PATH',
    "/data/ftp-pod/ftp/"
)

TITLE_SITE = getattr(TEMPLATE_VISIBLE_SETTINGS, 'TITLE_SITE', 'Pod')

# Add a Mediacourse recording
@csrf_protect
@staff_member_required(redirect_field_name='referrer')
def add_mediacourse_recording(request):
    # Used by URL like https://pod.univ.fr/mediacourses_add/?mediapath=4bdd6103-233b-40c1-b58a-87d26650cc34.zip&course_title=En cours d%27enregistrement 18 avr. 2019&recorder=1
    mediapath = request.GET.get('mediapath') if (request.GET.get('mediapath')) else ""
    course_title = request.GET.get('course_title') if request.GET.get('course_title') else ""
    recorder = request.GET.get('recorder') if request.GET.get('recorder') else 0

    # Check recorder existence corresponding to id
    try:
        oRecorder = Recorder.objects.get(id=recorder)
    except ObjectDoesNotExist:
        messages.add_message(request, messages.ERROR, _('Recorder doesn\'t exist.'))
        raise PermissionDenied

    # Generate path directory corresponding to the concerned recorder
    if oRecorder.directory != "":
        mediapath = os.path.join(DEFAULT_MEDIACOURSE_RECORDER_PATH, oRecorder.directory, mediapath)

    initial = {'title': course_title, 'mediapath': mediapath , 'recorder': recorder}

    # Check arguments
    if not mediapath and not request.user.is_superuser:
        messages.add_message(request, messages.ERROR, _('Mediapath should be indicated.'))
        raise PermissionDenied
	
    form = RecordingForm(request, initial=initial)

    # If the form has been submitted
    if request.method == 'POST':
        # A form bound to the POST data
        form = RecordingForm(request, request.POST)
        # All validation rules pass
        if form.is_valid():
            med = form.save(commit=False)
            med.save()
            message = _(
                'Your publication is saved.'
                ' Adding it to your videos will be in a few minutes.')
            messages.add_message(request, messages.INFO, message)
            return redirect(reverse('my_videos'))
        else:
            message = _('One or more errors have been found in the form.')
            messages.add_message(request, messages.ERROR, message)

    return render(request, "mediacourse/recordings_add.html", {"form": form})

# Notify that a Mediacourse recording was uploaded on the server
def notify_mediacourse_recording(request):
    # Used by URL like https://pod.univ.fr/mediacourses_notify/?recordingPlace=192_168_1_10&mediapath=file.zip&key=77fac92a3f06d50228116898187e50e5
    mediapath = request.GET.get('mediapath') if (request.GET.get('mediapath')) else ""
    recordingPlace = request.GET.get('recordingPlace') if (request.GET.get('recordingPlace')) else ""
    key = request.GET.get('key') if (request.GET.get('key')) else ""
    # Check arguments
    if recordingPlace and mediapath and key:
        recordingIpPlace = recordingPlace.replace("_", ".")
        try:
            # Check recorder existence corresponding to IP address
            recorder = Recorder.objects.get(address_ip=recordingIpPlace)
        except ObjectDoesNotExist:
            recorder = None
        if recorder:
            # Generate hashkey
            m = hashlib.md5()
            m.update(recordingPlace.encode('utf-8') + recorder.salt.encode('utf-8'))
            if key != m.hexdigest():
                return HttpResponse("nok : key is not valid")
            
            date_notify = datetime.now()
            formatted_date_notify = formats.date_format(date_notify, "SHORT_DATE_FORMAT")
            link_url = ''.join([request.build_absolute_uri(reverse('add_mediacourse_recording')), "?mediapath=", request.GET.get(
                'mediapath'), "&course_title=%s" % _("Recording"), " %s" % formatted_date_notify.replace("/", "-"), "&recorder=%s" % recorder.id])
            # Pointing to the URL of the CAS allows to reach the already authenticated form
            # URL like https://pod.univ.fr/sso-cas/login/?next=https%3A%2F%2Fpod.univ.fr%2Fmediacourses_add%2F%3Fmediapath%3Df18a5104-5a80-47a8-954e-7a142a67a935.zip%26course_title%3DEnregistrement%252021%2520juin%25202019%26recorder%3D1
            if USE_CAS:
                link_url = ''.join([request.build_absolute_uri('/'), "sso-cas/login/?next=", urllib.parse.quote_plus(link_url)])
    
            text_msg = _("Hello, \n\na new Mediacourse recording has just be added on the video website \"%(title_site)s\" from the recorder \"%(recorder)s\"."
                         "\nTo add it, just click on link below.\n\n%(link_url)s\nif you cannot click on link, just copy-paste it in your browser."
                         "\n\nRegards") % {'title_site': TITLE_SITE, 'recorder': recorder.name, 'link_url': link_url}
    
            html_msg = _("Hello, <p>a new Mediacourse recording has just be added on %(title_site)s from the recorder \"%(recorder)s\"."
                         "<br/>To add it, just click on link below.</p><a href=\"%(link_url)s\">%(link_url)s</a><br/><i>if you cannot click on link, just copy-paste it in your browser.</i>"
                         "<p><p>Regards</p>") % {'title_site': TITLE_SITE, 'recorder': recorder.name, 'link_url': link_url}
            # Sending the mail to the managers defined in the administration for the concerned Mediacourse recorder
            if recorder.user:
                admin_emails = [recorder.user.email]
            else:
                admin_emails = User.objects.filter(is_superuser=True).values_list('email', flat=True)
            subject = "[" + TITLE_SITE + \
                "] %s" % _('New Mediacourse recording added.')
            # Send the mail to the managers or admins (if not found)
            email_msg = EmailMultiAlternatives(subject, text_msg, settings.DEFAULT_FROM_EMAIL, admin_emails)

            email_msg.attach_alternative(html_msg, "text/html")
            email_msg.send(fail_silently=False)

            return HttpResponse("ok")
        else:
            return HttpResponse("nok : address_ip not valid")		
    else:
        return HttpResponse("nok : recordingPlace or mediapath or key are missing")
