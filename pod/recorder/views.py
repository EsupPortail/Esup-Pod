# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import os

from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from django.shortcuts import render
from django.conf import settings
from django.urls import reverse
from django.core.exceptions import PermissionDenied
from django.shortcuts import redirect
from django.contrib.admin.views.decorators import staff_member_required
from django.views.decorators.csrf import csrf_protect
from django.utils.translation import ugettext_lazy as _

from pod.recorder.models import Recorder, RecordingFileTreatment
from .forms import RecordingForm
from django.contrib import messages
import hashlib
from django.http import HttpResponse
from django.core.mail import EmailMultiAlternatives
from pod.main.context_processors import TEMPLATE_VISIBLE_SETTINGS
from django.contrib.auth.models import User
from django.core.exceptions import ObjectDoesNotExist
import urllib.parse


DEFAULT_RECORDER_PATH = getattr(
    settings, 'DEFAULT_RECORDER_PATH',
    "/data/ftp-pod/ftp/"
)

USE_CAS = getattr(settings, 'USE_CAS', False)
TITLE_SITE = getattr(TEMPLATE_VISIBLE_SETTINGS, 'TITLE_SITE', 'Pod')


def check_recorder(recorder, request):
    if recorder is None:
        messages.add_message(
            request, messages.ERROR, _('Recorder should be indicated.'))
        raise PermissionDenied
    try:
        recorder = Recorder.objects.get(id=recorder)
    except ObjectDoesNotExist:
        messages.add_message(
            request, messages.ERROR, _('Recorder not found.'))
        raise PermissionDenied
    return recorder


@csrf_protect
@staff_member_required(redirect_field_name='referrer')
def add_recording(request):
    mediapath = request.GET.get('mediapath') if (
        request.GET.get('mediapath')) else ""
    course_title = request.GET.get(
        'course_title') if request.GET.get('course_title') else ""
    recorder = request.GET.get('recorder') or None

    recorder = check_recorder(recorder, request)

    initial = {
        'title': course_title,
        'type': recorder.recording_type,
        'recorder': recorder,
        'user': request.user}

    if not mediapath and not request.user.is_superuser:
        messages.add_message(
            request, messages.ERROR, _('Mediapath should be indicated.'))
        raise PermissionDenied

    if mediapath != "":
        initial['source_file'] = "%s" % os.path.join(
            DEFAULT_RECORDER_PATH, mediapath)

    form = RecordingForm(request, initial=initial)

    if request.method == 'POST':  # If the form has been submitted...
        # A form bound to the POST data
        form = RecordingForm(request, request.POST)
        if form.is_valid():  # All validation rules pass
            med = form.save(commit=False)
            if request.POST.get('user') and request.POST.get('user') != "":
                med.user = form.cleaned_data['user']
            else:
                med.user = request.user
            """
            if (request.POST.get('mediapath')
                    and request.POST.get('mediapath') != ""):
                med.source_file = form.cleaned_data['mediapath']
            else:
                med.source_file = mediapath
            """
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


def reformat_url_if_use_cas(request, link_url):
    # Pointing to the URL of the CAS allows to reach the already
    # authenticated form URL like
    # https://pod.univ.fr/sso-cas/login/?next=https%3A%2F%2Fpod.univ
    # .fr%2Fadd_recording%2F%3Fmediapath%3Df18a5104-5a80-47a8-954e
    # -7a142a67a935.zip%26course_title%3DEnregistrement%252021
    # %2520juin%25202019%26recorder%3D1
    if USE_CAS:
        return ''.join(
            [request.build_absolute_uri('/'), "sso-cas/login/?next=",
             urllib.parse.quote_plus(link_url)])


def recorder_notify(request):

    # Used by URL like https://pod.univ.fr/recorder_notify/?recordingPlace
    # =192_168_1_10&mediapath=file.zip&key=77fac92a3f06d50228116898187e50e5
    mediapath = request.GET.get('mediapath') or ""
    recording_place = request.GET.get('recordingPlace') or ""
    course_title = request.GET.get('course_title') or ""
    key = request.GET.get('key') or ""
    # Check arguments
    if recording_place and mediapath and key:
        recording_ip_place = recording_place.replace("_", ".")
        try:
            # Check recorder existence corresponding to IP address
            recorder = Recorder.objects.get(address_ip=recording_ip_place)
        except ObjectDoesNotExist:
            recorder = None
        if recorder:
            # Generate hashkey
            m = hashlib.md5()
            m.update(recording_place.encode('utf-8') +
                     recorder.salt.encode('utf-8'))
            if key != m.hexdigest():
                return HttpResponse("nok : key is not valid")

            link_url = ''.join(
                [request.build_absolute_uri(reverse('add_recording')),
                 "?mediapath=", mediapath, "&course_title=%s" % course_title,
                 "&recorder=%s" % recorder.id])
            link_url = reformat_url_if_use_cas(request, link_url)

            text_msg = _(
                "Hello, \n\na new recording has just be added on the video "
                "website \"%(title_site)s\" from the recorder \"%("
                "recorder)s\". "
                "\nTo add it, just click on link below.\n\n%(link_url)s\nif "
                "you cannot click on link, just copy-paste it in your "
                "browser. "
                "\n\nRegards") % {'title_site': TITLE_SITE,
                                  'recorder': recorder.name,
                                  'link_url': link_url}

            html_msg = _(
                "Hello, <p>a new recording has just be added on %("
                "title_site)s from the recorder \"%(recorder)s\". "
                "<br/>To add it, just click on link below.</p><a href=\"%("
                "link_url)s\">%(link_url)s</a><br/><i>if you cannot click on "
                "link, just copy-paste it in your browser.</i> "
                "<p><p>Regards</p>") % {'title_site': TITLE_SITE,
                                        'recorder': recorder.name,
                                        'link_url': link_url}
            # Sending the mail to the managers defined in the administration
            # for the concerned recorder
            if recorder.user:
                admin_emails = [recorder.user.email]
            else:
                admin_emails = User.objects.filter(is_superuser=True)\
                    .values_list('email', flat=True)
            subject = "[" + TITLE_SITE + \
                      "] %s" % _('New recording added.')
            # Send the mail to the managers or admins (if not found)
            email_msg = EmailMultiAlternatives(subject, text_msg,
                                               settings.DEFAULT_FROM_EMAIL,
                                               admin_emails)

            email_msg.attach_alternative(html_msg, "text/html")
            email_msg.send(fail_silently=False)
            return HttpResponse("ok")
        else:
            return HttpResponse("nok : address_ip not valid")
    else:
        return HttpResponse("nok : recordingPlace or mediapath or key are "
                            "missing")


@csrf_protect
@login_required(redirect_field_name='referrer')
@staff_member_required(redirect_field_name='referrer')
def claim_record(request):
    # get records list ordered by date
    records_list = RecordingFileTreatment.objects.\
        filter(require_manual_claim=True).order_by('-date_added')
    page = request.GET.get('page', 1)

    full_path = ""
    if page:
        full_path = request.get_full_path().replace(
            "?page=%s" % page, "").replace("&page=%s" % page, "")

    paginator = Paginator(records_list, 12)
    try:
        records = paginator.page(page)
    except PageNotAnInteger:
        records = paginator.page(1)
    except EmptyPage:
        records = paginator.page(paginator.num_pages)

    if request.is_ajax():
        return render(
            request, 'recorder/record_list.html',
            {'records': records, "full_path": full_path})

    return render(request, 'recorder/claim_record.html', {
        'records': records, "full_path": full_path
    })
