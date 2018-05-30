from django.http import HttpResponse
from django.shortcuts import render
from django.shortcuts import redirect
from django.urls import reverse
from django.conf import settings

from django_cas.decorators import gateway

USE_CAS = getattr(
    settings, 'USE_CAS', False)
CAS_GATEWAY = getattr(
    settings, 'CAS_GATEWAY', False)

if CAS_GATEWAY:
    @gateway()
    def authentication_login_gateway(request):
        next = request.GET['next'] if request.GET.get('next') else '/'
        if request.user.is_authenticated():
            return redirect(next)

        return render(request, 'authentication/login.html', {
            'USE_CAS': USE_CAS, 'referrer': next
        })
else:
    def authentication_login_gateway(request):
        return HttpResponse(
            "You must set CAS_GATEWAY to True to use this view")


def authentication_login(request):
    referrer = request.GET['referrer'] if request.GET.get('referrer') else '/'
    if request.user.is_authenticated():
        return redirect(referrer)
    if USE_CAS and CAS_GATEWAY:
        url = reverse('authentication_login_gateway')
        url += '?next=%s' % referrer
        return redirect(url)
    elif USE_CAS:
        return render(request, 'authentication/login.html', {
            'USE_CAS': USE_CAS, 'referrer': referrer
        })
    else:
        url = reverse('local-login')
        url += '?next=%s' % referrer
        return redirect(url)


def authentication_logout(request):
    if USE_CAS:
        return redirect('django_cas:logout')
    else:
        url = reverse('local-logout')
        url += '?next=/'
        return redirect(url)
