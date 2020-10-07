# -*- coding: utf-8 -*-
from __future__ import unicode_literals

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
from pod.bbb.models import Meeting
from .forms import MeetingForm
from django.contrib import messages
from django.shortcuts import get_object_or_404

USE_BBB = getattr(settings, 'USE_BBB', False)


@csrf_protect
@login_required(redirect_field_name='referrer')
@staff_member_required(redirect_field_name='referrer')
def list_meeting(request):
    # Get meetings list, which recordings are available, ordered by date
    meetings_list = Meeting.objects.\
        filter(user__user_id=request.user.id, recording_available=True)
    meetings_list = meetings_list.order_by('-date')
    # print(str(meetings_list.query))

    page = request.GET.get('page', 1)

    full_path = ""
    if page:
        full_path = request.get_full_path().replace(
            "?page=%s" % page, "").replace("&page=%s" % page, "")

    paginator = Paginator(meetings_list, 12)
    try:
        records = paginator.page(page)
    except PageNotAnInteger:
        records = paginator.page(1)
    except EmptyPage:
        records = paginator.page(paginator.num_pages)

    if request.is_ajax():
        return render(
            request, 'bbb/record_list.html',
            {'records': records, "full_path": full_path})

    return render(request, 'bbb/list_meeting.html', {
        'records': records, "full_path": full_path
    })


@csrf_protect
@staff_member_required(redirect_field_name='referrer')
def publish_meeting(request, id=None):
    # Allows you to create a video from a BigBlueButton presentation

    record = get_object_or_404(Meeting, id=id)

    initial = {
        'id': record.id,
        'meeting_id': record.meeting_id,
        'internal_meeting_id': record.internal_meeting_id,
        'meeting_name': record.meeting_name,
        'recorded': record.recorded,
        'recording_available': record.recording_available,
        'recording_url': record.recording_url,
        'thumbnail_url': record.thumbnail_url,
        'date': record.date}

    form = MeetingForm(request, initial=initial)

    # Check security : a normal user can publish only a meeting
    # where he was moderator
    meetings_list = Meeting.objects.\
        filter(user__user_id=request.user.id, id=id)
    if not meetings_list and not request.user.is_superuser:
        messages.add_message(
            request, messages.ERROR,
            _(u'You aren\'t the moderator of this BigBlueButton session.'))
        raise PermissionDenied

    if request.method == "POST":
        form = MeetingForm(request, request.POST)
        if form.is_valid():
            meeting = form.save(commit=False)
            meeting.id = record.id
            # The 2 parameters are very important in the publish process :
            # At this stage, we put encoding_step=1 (waiting for encoding)
            # and the encoded_by = user that convert this presentation.
            # See the impacts in the models.py, process_recording function.
            # Waiting for encoding
            meeting.encoding_step = 1
            # Save the user that convert this presentation
            meeting.encoded_by = request.user
            meeting.save()
            messages.add_message(
                request, messages.INFO,
                _(u'The BigBlueButton session has been published.'))
            return redirect(
                reverse('bbb:list_meeting')
            )
        else:
            messages.add_message(
                request, messages.ERROR,
                _(u'One or more errors have been found in the form.'))

    return render(request, 'bbb/publish_meeting.html', {
        'record': record,
        'form': form}
    )
