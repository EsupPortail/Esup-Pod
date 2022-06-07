import datetime
from genericpath import exists
import logging
from multiprocessing import context
from django.conf import settings
from django.http import (HttpResponse, HttpResponseNotFound, HttpResponseRedirect)
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

RESTRICT_EDIT_MEETING_ACCESS_TO_STAFF_ONLY = getattr(
    settings, "RESTRICT_EDIT_MEETING_ACCESS_TO_STAFF_ONLY", False
)

@csrf_protect
@login_required(redirect_field_name="referrer")
def meeting(request):
    # attention, pas toutes les meetings mais seulement celles de l'utilsiateur connecté
    # a faire ! --> 'dataMeetings':Meetings.objects.filter(owner==request.user, sites=get_current_site(request), additional_owner)
    return render(request, 'meeting.html', {'dataMeetings':Meetings.objects.all()})


@csrf_protect
@login_required(redirect_field_name="referrer")
def create(request):

  if RESTRICT_EDIT_MEETING_ACCESS_TO_STAFF_ONLY and request.user.is_staff is False:
    return render(request, "meeting_edit.html", {"access_not_allowed": True})

  form = MeetingsForm(
    is_staff=request.user.is_staff,
    is_superuser=request.user.is_superuser,
  )

  if request.method == "POST":
    form = MeetingsForm(
      request.POST,
      is_staff=request.user.is_staff,
      is_superuser=request.user.is_superuser,
    )
    if form.is_valid():
      meeting = form.save(commit=False)
      if (
        (request.user.is_superuser or request.user.has_perm("meeting.add_meeting"))
        and request.POST.get("owner")
        and request.POST.get("owner") != ""
      ):
        meeting.owner = form.cleaned_data["owner"]
      elif getattr(meeting, "owner", None) is None:
        meeting.owner = request.user
      meeting.save()
      form.save_m2m()
      meeting.sites.add(get_current_site(request))
      meeting.save()
      form.save_m2m()
      
      messages.add_message(
        request, messages.INFO, ("The changes have been saved.")
      )
      return redirect(reverse("meetings:meeting"))
    else:
      messages.add_message(
        request,
        messages.ERROR,
        ("One or more errors have been found in the form."),
      )
  context={"form": form}

  return render(request, "meeting_add.html", context)

@csrf_protect
@login_required(redirect_field_name="referrer")
def delete_meeting(request, meetingID):
    # utiliser le get object or 404 sites=get_current_site(request)
    meeting = get_object_or_404(Meetings, meetingID=meetingID, sites=get_current_site(request))

    if request.user != meeting.owner and not (
        request.user.is_superuser or request.user.has_perm("meeting.delete_meeting")
    ):
        messages.add_message(request, messages.ERROR, ("You cannot delete this meeting."))
        raise PermissionDenied

    if request.method == "POST": # verifier que le user connecté est bien le prop de la reunion !
      meeting.delete()
      return redirect(reverse("meetings:meeting"))

    context={'item':meeting}

    return render(request, "meeting_delete.html", context)


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
    if request.user.is_authenticated and (request.user == meeting.owner or request.user in meeting.additional_owners):
      name = request.user.get_full_name()
      url = meeting.join_url(request.user.get_full_name(), meeting.moderator_password)
      #return url
    else:
      form = JoinForm()
      url = meeting.join_url(request.user.get_full_name(), meeting.moderator_password)
      #return url

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
    ''' 
    # recup l'id numérique dans le meetingID puis chercher si elle existe sinon 404 sites=get_current_site(request)
    meeting = get_object_or_404(Meetings, meetingID=meetingID, sites=get_current_site(request))
    if request.method == "POST":
        form = JoinForm(request.POST)
        if form.is_valid():
          data = form.cleaned_data
          name = data.get('name')
          password = data.get('password')

          return HttpResponseRedirect(Meetings.join_url(name, password))
    else:
        form = JoinForm()

    context={'item':meeting,
            'form':form}

    return render(request, 'meeting_join.html', context)

def edit_meeting(request, meetingID):
  # get object or 404 ! sites=get_current_site(request)

  '''
  meeting = Meetings.objects.get(meetingID=meetingID)
  default_owner = meeting.owner.pk if meeting else request.user.pk
  form = MeetingsForm(
      instance=meeting,
      initial={"owner": default_owner},
    )

  if request.method == "POST":
    form = MeetingsForm(request.POST, instance=meeting,)
    if form.is_valid():
        meeting = form.save(commit=False)
        meeting.owner = request.user
        meeting.save()
        messages.add_message(
            request, messages.INFO, ("The changes have been saved.")
        )
    else:
      messages.add_message(
        request,
        messages.ERROR,
        ("One or more errors have been found in the form."),
      )

    return redirect('/meeting')

  context={"form": form}

  return render(request, "meeting_edit.html", context)
  '''

  meeting = get_object_or_404(Meetings, meetingID=meetingID, sites=get_current_site(request))

  if RESTRICT_EDIT_MEETING_ACCESS_TO_STAFF_ONLY and request.user.is_staff is False:
    return render(request, "meeting_edit.html", {"access_not_allowed": True})

  if (
    meeting
    and request.user != meeting.owner
    and (
        not (request.user.is_superuser or request.user.has_perm("meeting.change_meeting"))
    )
    and (request.user not in meeting.additional_owners.all())
  ):
    messages.add_message(request, messages.ERROR, ("You cannot edit this meeting."))
    raise PermissionDenied

  default_owner = meeting.owner.pk if meeting else request.user.pk
  form = MeetingsForm(
    instance=meeting,
    is_staff=request.user.is_staff,
    is_superuser=request.user.is_superuser,
    initial={"owner": default_owner},
  )

  if request.method == "POST":
    form = MeetingsForm(
      request.POST,
      request.FILES,
      instance=meeting,
      is_staff=request.user.is_staff,
      is_superuser=request.user.is_superuser,
    )
    if form.is_valid():
      meeting = form.save(commit=False)
      if (
        (request.user.is_superuser or request.user.has_perm("meeting.add_meeting"))
        and request.POST.get("owner")
        and request.POST.get("owner") != ""
      ):
        meeting.owner = form.cleaned_data["owner"]

      elif getattr(meeting, "owner", None) is None:
        meeting.owner = request.user
        
      meeting.save()
      form.save_m2m()
      meeting.sites.add(get_current_site(request))
      meeting.save()
      form.save_m2m()

      messages.add_message(
        request, messages.INFO, ("The changes have been saved.")
      )
      return redirect('/meeting')
    else:
      messages.add_message(
        request,
        messages.ERROR,
        ("One or more errors have been found in the form."),
      )

  context={"form": form}

  return render(request, "meeting_edit.html", context)