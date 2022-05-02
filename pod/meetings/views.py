from django.http import (HttpResponse)
from django.shortcuts import get_object_or_404, render

from pod.meetings.models import Meetings

def index(request):
    return render(request, "meeting.html")

def add(request, slug):
    ajout = get_object_or_404(Meetings, slug=slug)
    return render(request, "add.html")