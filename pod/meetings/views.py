from django.http import (HttpResponse, HttpResponseRedirect)
from django.shortcuts import redirect, render, get_object_or_404
from django.template import loader
from django.urls import reverse
#from pod.meetings.filters import MeetingsFilter
from pod.meetings.forms import MeetingsForm

from pod.meetings.models import Meetings

def index(request):

  return render(request, 'meeting.html', {'dataMeetings':Meetings.objects.all()})

def add(request):
  print("add")
  if request.method == "POST":
    print('POST')
    form = MeetingsForm(request.POST)
    if form.is_valid():
      meeting = form.save()
      print(meeting, meeting.id)
      
      return redirect('/meeting')
  else:
    form = MeetingsForm()

  return render(request, 'meeting_add.html', {'form': form})

'''
def delete(request, meeting_id):
  meeting = Meetings.objects.get(meeting_id=meeting_id)
  meeting.delete()
  return HttpResponseRedirect(reverse('index'))
'''