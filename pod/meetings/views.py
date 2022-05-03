from django.http import (HttpResponse, HttpResponseRedirect)
from django.shortcuts import redirect, render
from django.template import loader
from django.urls import reverse
from pod.meetings.forms import MeetingsForm

from pod.meetings.models import Meetings

def index(request):
  return render(request, 'meeting.html')

def add(request):
  if request.method == "POST":
    form = MeetingsForm(request.POST)
    if form.is_valid:
      form.save()
      return redirect('/meeting')
  else:
    form = MeetingsForm()

  return render(request, 'index.html', {'form': form, 'dataMeetings':Meetings.objects.all()})