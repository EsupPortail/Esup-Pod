from django.http import HttpResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_protect

from django_cas.decorators import gateway

@gateway()
def authenticate(request):
    #stuff
    #todo fill the next value
    #if authenticate:
    #    redirect to next
    return render(request, 'foo/bar.html')