from django.core.urlresolvers import reverse
from django.http import HttpResponse
from django.http import HttpResponseRedirect
from django.shortcuts import render_to_response
from django.views.decorators.csrf import csrf_protect

@csrf_protect
def video_completion(request, slug):
	return HttpResponse('TODO')

@csrf_protect
def video_completion_contributor(request, slug):
	return HttpResponse('TODO')

@csrf_protect
def video_completion_document(request, slug):
	return HttpResponse('TODO')

@csrf_protect
def video_completion_track(request, slug):
	return HttpResponse('TODO')

@csrf_protect
def video_completion_overlay(request, slug):
	return HttpResponse('TODO')