from django.http import HttpResponse
from django.shortcuts import render
from django.shortcuts import redirect
from django.urls import reverse
from django.conf import settings
from django.views.decorators.csrf import csrf_protect
from django.contrib import messages
from django.utils.translation import ugettext_lazy as _
from django.contrib.auth.decorators import login_required

from django_cas.decorators import gateway

from pod.authentication.forms import FrontOwnerForm

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
    iframe_param = 'is_iframe=true&' if (
        request.GET.get('is_iframe')) else ''
    if request.user.is_authenticated():
        return redirect(referrer)
    if USE_CAS and CAS_GATEWAY:
        url = reverse('authentication_login_gateway')
        url += '?%snext=%s' % (iframe_param, referrer)
        return redirect(url)
    elif USE_CAS:
        return render(request, 'authentication/login.html', {
            'USE_CAS': USE_CAS, 'referrer': referrer
        })
    else:
        url = reverse('local-login')
        url += '?%snext=%s' % (iframe_param, referrer)
        return redirect(url)


def authentication_logout(request):
    if USE_CAS:
        return redirect('django_cas:logout')
    else:
        url = reverse('local-logout')
        url += '?next=/'
        return redirect(url)


@csrf_protect
@login_required(redirect_field_name='referrer')
def userpicture(request):

    frontOwnerForm = FrontOwnerForm(instance=request.user.owner)

    if request.method == "POST":
        frontOwnerForm = FrontOwnerForm(
            request.POST, instance=request.user.owner)
        if frontOwnerForm.is_valid():
            frontOwnerForm.save()
            messages.add_message(
                request, messages.INFO, _('Your picture has been saved.'))
        else:
            messages.add_message(
                request, messages.ERROR,
                _(u'One or more errors have been found in the form.'))

    return render(request, 'userpicture/userpicture.html', {
        'frontOwnerForm': frontOwnerForm}
    )
