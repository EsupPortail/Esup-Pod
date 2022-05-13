import datetime
from genericpath import exists
import logging
from django.http import (HttpResponse, HttpResponseRedirect)
from django.shortcuts import redirect, render, get_object_or_404
from django.urls import reverse
from django.contrib import messages
from platformdirs import user_data_path
from pod.meetings.forms import MeetingsForm, JoinForm
from pod.meetings.models import Meetings, User

from django.views.decorators.csrf import csrf_protect
from django.contrib.auth.decorators import login_required, user_passes_test
from django.core.exceptions import SuspiciousOperation
from django.contrib.sites.shortcuts import get_current_site
from django.core.exceptions import PermissionDenied

from pod.video.views import is_in_video_groups

@csrf_protect
@login_required(redirect_field_name="referrer")
def meeting(request):
  # attention, pas toutes les meetings mais seulement celles de l'utilsiateur connecté

  return render(request, 'meeting.html', {'dataMeetings':Meetings.objects.all()})

@csrf_protect
@login_required(redirect_field_name="referrer")
def create(request):
  print("add")
  if request.method == "POST":
    print('POST')
    form = MeetingsForm(request.POST)
    if form.is_valid():
      meeting = form.save(commit=False)
      meeting.owner = request.user
      meeting.save()
      print(meeting, meeting.meetingID)
      
      return redirect('/meeting')
  else:
    form = MeetingsForm()

  return render(request, 'meeting_add.html', {'form': form})

def delete_meeting(request, meeting_id):
    if request.method == "POST":
        Meetings.end_meeting(meeting_id)

        msg = 'Successfully ended meeting %s' % meeting_id
        messages.success(request, msg)
        return redirect('/meeting')
    else:
        msg = 'Unable to end meeting %s' % meeting_id
        messages.error(request, msg)
        return redirect('/meeting')

def join_meeting(request, meetingID, slug_private=None):
    '''
    try:
        id = int(meetingID[: meetingID.find("-")])
    except ValueError:
        raise SuspiciousOperation("Invalid meeting id")
    meeting = get_object_or_404(Meetings, id=id, sites=get_current_site(request))

    is_draft = meeting.is_draft
    is_restricted = meeting.is_restricted
    is_restricted_to_group = meeting.restrict_access_to_groups.all().exists()
    is_access_protected = (
        is_draft
        or is_restricted
        or is_restricted_to_group
        # or is_password_protected
    )

    if is_access_protected:
        access_granted_for_private = slug_private and slug_private == meeting.get_hashkey()
        access_granted_for_draft = request.user.is_authenticated and (
            request.user == meeting.owner
            or request.user.is_superuser
            or request.user.has_perm("meeting.change_meeting")
            or (request.user in meeting.additional_owners.all())
        )
        access_granted_for_restricted = (
            request.user.is_authenticated and not is_restricted_to_group
        )
        access_granted_for_group = (
            (request.user.is_authenticated and is_in_video_groups(request.user, meeting))
            or request.user == meeting.owner
            or request.user.is_superuser
            or request.user.has_perm("recorder.add_recording")
            or (request.user in meeting.additional_owners.all())
        )

        return (
            access_granted_for_private
            or (is_draft and access_granted_for_draft)
            or (is_restricted and access_granted_for_restricted)
            # and is_password_protected is False)
            or (is_restricted_to_group and access_granted_for_group)
            # and is_password_protected is False)
            # or (
            #     is_password_protected
            #     and access_granted_for_draft
            # )
            # or (
            #     is_password_protected
            #     and request.POST.get('password')
            #     and request.POST.get('password') == video.password
            # )
        )
      '''
    # verifier si la reunion est commencé ou pas
    # si elle est déjà terminé // comparer à la date de fin
    # si la personne est owner ou additionnal owner
    # si la conf n'existe pas, il faut la créer, si elle existe, il faut rediriger vers cette reunion
    # url = meeting.join_url(request.user.get_full_name(), meeting.moderator_password) 
    # recuperer
    # si la personne n'est pas owner (ou additionnal owner)
    # si la conf n'existe pas --> bye
    # si elle existe
    # si elle est pas démarrer, page attente

    '''
    if Meetings.owner or Meetings.additional_owners:
      if request.user.is_authenticated :
        name = request.user.username
        url = Meetings.join_url(request.user.get_full_name(), Meetings.moderator_password)
        return url
    else:
      form = JoinForm()
      url = Meetings.join_url(request.user.get_full_name(), Meetings.moderator_password)
      return url
    '''

    current_datetime = datetime.datetime.now()
    if meetingID == 'meeting-ended':
      try:
          attributes = e['attributes']
          meetingID = attributes['meeting']['external-meeting-id']

          meeting = Meetings.objects.filter(meeting_id=meetingID).first()

          Meetings.objects.filter(
            meeting=meeting,
            end_date__isnull=True
          ).update(
            end_date=current_datetime
          )
      except Exception as e:
        logging.error(str(e))

    
    if meetingID is not exists:
      if request.method == "POST":
        print('POST')
      form = MeetingsForm(request.POST)
      if form.is_valid():
        meeting = form.save(commit=False)
        meeting.owner = request.user
        meeting.save()
        print(meeting, meeting.meetingID)
    else:
      url = Meetings.join_url(request.user.get_full_name(), meeting.moderator_password)
      return url

    if (
      request.POST.get("password")
      and request.POST.get("password") != meeting.password
      ):
        messages.add_message(
        request, messages.ERROR, ("The password is incorrect.")
        )

    elif request.user.is_authenticated:
            messages.add_message(
                request, messages.ERROR, ("You cannot enter in the meeting.")
            )
            raise PermissionDenied

    if request.method == "POST":
        form = JoinForm(request.POST)
        if form.is_valid():

          return redirect('/meeting/')
    else:
        form = JoinForm()

    return render(request, 'meeting_join.html', {'form': form})

def edit_meeting(request):
  if request.method == "POST":
        form = MeetingsForm(
            request.POST,
            request.FILES,
            instance=meeting,
            is_staff=request.user.is_staff,
            is_superuser=request.user.is_superuser,
            current_user=request.user,
            current_lang=request.LANGUAGE_CODE,
        )
        if form.is_valid():
            meeting = form.save(request, form)
            messages.add_message(
                request, messages.INFO, ("The changes have been saved.")
            )
            if request.POST.get("_saveandsee"):
                return redirect(reverse("video", args=(meeting.meetingID,)))
            else:
                return redirect(reverse("meeting_edit", args=(meeting.meetingID,)))
        else:
            messages.add_message(
                request,
                messages.ERROR,
                ("One or more errors have been found in the form."),
            )
  return render(request, "meeting/meeting_edit.html", {"form": form})