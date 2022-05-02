from django.http import (HttpResponse, HttpResponseRedirect)
from django.shortcuts import render
from django.template import loader
from django.urls import reverse

from pod.meetings.models import Meetings

def index(request):
    return render(request, 'meeting.html')

def add(request):
  template = loader.get_template('add.html')
  return HttpResponse(template.render({}, request))