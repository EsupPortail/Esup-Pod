from django.shortcuts import render
from django.http import HttpResponse
# Create your views here.
def homepage(request):
    return render(request, 'custom/pod_home.html', {})
