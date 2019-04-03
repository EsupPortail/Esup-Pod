from pod.main.forms import ContactUsForm, SUBJECT_CHOICES
from pod.main.context_processors import TEMPLATE_VISIBLE_SETTINGS
from django.shortcuts import render
from django.contrib.sites.shortcuts import get_current_site
from django.contrib import messages
from django.conf import settings
from django.views.decorators.csrf import csrf_protect
from django.template import loader
from django.core.mail import EmailMultiAlternatives
from django.utils.translation import ugettext_lazy as _
from django.shortcuts import redirect
from django.contrib.auth.models import User
from django.core.exceptions import PermissionDenied

from django.http import HttpResponse
from wsgiref.util import FileWrapper

from pod.video.models import Video
import os
import mimetypes

TITLE_SITE = getattr(TEMPLATE_VISIBLE_SETTINGS, 'TITLE_SITE', 'Pod')
CONTACT_US_EMAIL = getattr(
    settings, 'CONTACT_US_EMAIL', [
        mail for name, mail in getattr(settings, 'MANAGERS')])
DEFAULT_FROM_EMAIL = getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@univ.fr')


@csrf_protect
def download_file(request):
    if request.POST and request.POST.get("filename"):
        filename = os.path.join(
            settings.MEDIA_ROOT, request.POST["filename"])
        wrapper = FileWrapper(open(filename, 'rb'))
        response = HttpResponse(
            wrapper, content_type=mimetypes.guess_type(filename)[0])
        response['Content-Length'] = os.path.getsize(filename)
        response[
            'Content-Disposition'
        ] = 'attachment; filename="%s"' % os.path.basename(filename)
        return response
    else:
        raise PermissionDenied


@csrf_protect
def contact_us(request):
    owner = User.objects.get(id=request.GET.get('owner')) if (
        request.GET.get('owner')
        and User.objects.filter(id=request.GET.get('owner')).first()) else None

    video = Video.objects.get(id=request.GET.get('video')) if (
        request.GET.get('video')
        and Video.objects.filter(
            id=request.GET.get('video')).first()
    ) else None

    description = "%s: %s\n%s: %s%s\n\n" % (
        _('Title'),
        video.title, _('Link'),
        'https:' if request.is_secure() else 'http:',
        video.get_full_url(request)) if video else None

    send_subject = request.GET.get('subject') if (
        request.GET.get('subject')
        and request.GET.get('subject') in [
            key for key, value in SUBJECT_CHOICES
        ]) else None

    prefix = 'https://' if request.is_secure() else 'http://'
    home_page = ''.join([prefix, get_current_site(request).domain])
    url_referrer = request.META["HTTP_REFERER"] if request.META.get(
        "HTTP_REFERER") else home_page

    form = ContactUsForm(
        request,
        initial={'url_referrer': url_referrer,
                 'subject': send_subject, 'description': description})

    if request.method == "POST":
        form = ContactUsForm(request, request.POST)
        if form.is_valid():
            name = form.cleaned_data['name']
            form_subject = form.cleaned_data['subject'] if (
                form.cleaned_data.get('subject')
            ) else send_subject
            subject = "[ %s ] %s" % (
                TITLE_SITE,
                dict(SUBJECT_CHOICES)[form_subject])
            email = form.cleaned_data['email']
            message = form.cleaned_data['description']

            text_content = loader.get_template('mail/mail.txt').render({
                'name': name,
                'email': email,
                'TITLE_SITE': TITLE_SITE,
                'message': message,
                'url_referrer': form.cleaned_data['url_referrer']
            })
            html_content = loader.get_template('mail/mail.html').render({
                'name': name,
                'email': email,
                'TITLE_SITE': TITLE_SITE,
                'message': message.replace("\n", "<br/>"),
                'url_referrer': form.cleaned_data['url_referrer']
            })
            #dest_email = [owner.email] if owner else CONTACT_US_EMAIL

            CONTACT_US_EMAIL = getattr(settings, 'CONTACT_US_EMAIL', [])
            dest_email = []

            if CONTACT_US_EMAIL:
                if video_to_encode.owner.owner.establishment.lower() == "u123":
                    dest_email.append(CONTACT_US_EMAIL[0][1])
                else:
                    dest_email.append(CONTACT_US_EMAIL[1][1])

            msg = EmailMultiAlternatives(
                subject, text_content, email, dest_email)
            msg.attach_alternative(html_content, "text/html")
            msg.send(fail_silently=False)

            # EMAIL TO SENDER
            subject = "[ %s ] %s %s" % (
                TITLE_SITE, _('your message untitled'),
                dict(SUBJECT_CHOICES)[form_subject])

            text_content = loader.get_template('mail/mail_sender.txt').render(
                {
                    'TITLE_SITE': TITLE_SITE,
                    'message': message
                })
            html_content = loader.get_template('mail/mail_sender.html').render(
                {
                    'TITLE_SITE': TITLE_SITE,
                    'message': message.replace("\n", "<br/>")
                })
            msg = EmailMultiAlternatives(
                subject, text_content, DEFAULT_FROM_EMAIL, [email])
            msg.attach_alternative(html_content, "text/html")
            msg.send(fail_silently=False)

            messages.add_message(
                request, messages.INFO, _('Your message have been sent.'))

            return redirect(form.cleaned_data['url_referrer'])

        else:
            messages.add_message(
                request, messages.ERROR,
                _(u'One or more errors have been found in the form.'))

    return render(request, 'contact_us.html', {
        'form': form,
        'owner': owner}
    )
