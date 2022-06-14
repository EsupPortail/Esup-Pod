import datetime
from genericpath import exists
import logging
from multiprocessing import context
from re import template
from django.conf import settings
from django.http import (HttpResponse, HttpResponseNotFound, HttpResponseRedirect)
from django.shortcuts import redirect, render, get_object_or_404
from django.urls import reverse
from django.contrib import messages
from platformdirs import user_data_path
from django.utils.translation import ugettext_lazy as _
from pod.meetings.forms import MeetingsForm, MeetingsNameForm
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
def create_meeting(request):

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
      msg = 'Successfully created meeting'
      messages.success(request, msg)
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

    try:
        id = int(meetingID[: meetingID.find("-")])
    except ValueError:
        raise SuspiciousOperation("Invalid meeting id")
    meeting = get_object_or_404(Meetings, id=id, sites=get_current_site(request))

    if request.user.is_authenticated and (request.user == meeting.owner or request.user in meeting.additional_owners):
      name = request.user.get_full_name()
      url = Meetings.join_url(meetingID, name, password=meeting.attendee_password)
      print("is moderator : %s" % url)

    if request.method == "POST":
        form = MeetingsNameForm(request.POST, is_staff=request.user.is_staff, is_superuser=request.user.is_superuser)
        if form.is_valid():
          data = form.cleaned_data
          meetingID = data.get('meetingID')
          name = data.get('name')
          password = data.get('password')

          return HttpResponseRedirect(Meetings.join_url(meetingID, name, password))
    else:
        form = MeetingsNameForm(is_staff=request.user.is_staff, is_superuser=request.user.is_superuser)

    context={'meeting':meeting,
            'form':form}

    return render(request, "meeting_join.html", context)

def is_in_meeting_groups(user, meeting):
  return user.owner.accessgroup_set.filter(
    code_name__in=[
      name[0] for name in meeting.restrict_access_to_groups.values_list("code_name")
    ]
  ).exists()

def get_meeting_access(request, meeting, slug_private):
  """Return True if access is granted to current user."""
  is_draft = meeting.is_draft
  is_restricted = meeting.is_restricted
  is_restricted_to_group = meeting.restrict_access_to_groups.all().exists()
  """
  is_password_protected = (video.password is not None
                          and video.password != '')
  """
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
      (request.user.is_authenticated and is_in_meeting_groups(request.user, meeting))
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

  else:
    return True

def render_meeting(request, meetingID, template_meeting="meeting_join.html", slug_private=None):
  meeting = get_object_or_404(Meetings, meetingID=meetingID, sites=get_current_site(request))

  is_password_protected = meeting.attendee_password is not None and meeting.attendee_password != ""

  show_page = get_meeting_access(request, meeting, slug_private)

  if (
    (show_page and not is_password_protected)
    or (
      show_page
      and is_password_protected
      and request.POST.get("password")
      and request.POST.get("password") == meeting.attendee_password
    )
    or (slug_private and slug_private == meeting.get_hashkey())
    or request.user == meeting.owner
    or request.user.is_superuser
    or request.user.has_perm("meeting.change_meeting")
    or (request.user in meeting.additional_owners.all())
  ):
    return render(
      request,
      template_meeting,
      {
        "meeting": meeting,
      },
    )
  else:
    is_draft = meeting.is_draft
    is_restricted = meeting.is_restricted
    is_restricted_to_group = meeting.restrict_access_to_groups.all().exists()
    is_access_protected = is_draft or is_restricted or is_restricted_to_group
    if is_password_protected and (
      not is_access_protected or (is_access_protected and show_page)
    ):
      form = (
        MeetingsNameForm(request.POST) if request.POST else MeetingsNameForm()
      )
      if (
        request.POST.get("password")
        and request.POST.get("password") != meeting.attendee_password
      ):
        messages.add_message(
          request, messages.ERROR, _("The password is incorrect.")
        )
      return render(
        request,
        "meeting.html",
        {
          "meeting": meeting,
          "form": form,
        },
      )
    else:
      iframe_param = "is_iframe=true&" if (request.GET.get("is_iframe")) else ""
      return redirect(
        "%s?%sreferrer=%s"
        % (settings.LOGIN_URL, iframe_param, request.get_full_path())
      )

def edit_meeting(request, meetingID):
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
      return redirect(reverse("meetings:meeting"))
    else:
      messages.add_message(
        request,
        messages.ERROR,
        ("One or more errors have been found in the form."),
      )

  context={"form": form}

  return render(request, "meeting_edit.html", context)