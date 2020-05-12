from pod.main.forms import ContactUsForm, SUBJECT_CHOICES
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
from django.db.models import Count
from django.http import HttpResponse, HttpResponseBadRequest
from wsgiref.util import FileWrapper
from django.db.models import Q
from pod.video.models import Video
import os
import mimetypes
import json
import unicodedata
from django.contrib.auth.decorators import login_required

##
# Settings exposed in templates
#
TEMPLATE_VISIBLE_SETTINGS = getattr(
    settings,
    'TEMPLATE_VISIBLE_SETTINGS',
    {
        'TITLE_SITE': 'Pod',
        'TITLE_ETB': 'University name',
        'LOGO_SITE': 'img/logoPod.svg',
        'LOGO_ETB': 'img/logo_etb.svg',
        'LOGO_PLAYER': 'img/logoPod.svg',
        'LINK_PLAYER': '',
        'FOOTER_TEXT': ('',),
        'FAVICON': 'img/logoPod.svg',
        'CSS_OVERRIDE': '',
        'PRE_HEADER_TEMPLATE': '',
        'POST_FOOTER_TEMPLATE': '',
        'TRACKING_TEMPLATE': '',
    }
)

TITLE_SITE = getattr(TEMPLATE_VISIBLE_SETTINGS, 'TITLE_SITE', 'Pod')
CONTACT_US_EMAIL = getattr(
    settings, 'CONTACT_US_EMAIL', [
        mail for name, mail in getattr(settings, 'MANAGERS')])
DEFAULT_FROM_EMAIL = getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@univ.fr')
USER_CONTACT_EMAIL_CASE = getattr(
        settings, 'USER_CONTACT_EMAIL_CASE', [])
CUSTOM_CONTACT_US = getattr(
        settings, 'CUSTOM_CONTACT_US', False)
MANAGERS = getattr(settings, "MANAGERS", [])
USE_ESTABLISHMENT = getattr(
        settings, 'USE_ESTABLISHMENT_FIELD', False)
USER_CONTACT_EMAIL_CASE = getattr(
        settings, 'USER_CONTACT_EMAIL_CASE', [])
CUSTOM_CONTACT_US = getattr(
        settings, 'CUSTOM_CONTACT_US', False)
SUPPORT_EMAIL = getattr(
    settings, "SUPPORT_EMAIL", []
)
USE_SUPPORT_EMAIL = getattr(
        settings, "USE_SUPPORT_EMAIL", False)
HIDE_USERNAME = getattr(
        settings, 'HIDE_USERNAME', False)
MENUBAR_HIDE_INACTIVE_OWNERS = getattr(
        settings, 'HIDE_USERNAME', True)
MENUBAR_SHOW_STAFF_OWNERS_ONLY = getattr(
        settings, 'MENUBAR_SHOW_STAFF_OWNERS_ONLY', False)
HIDE_USER_TAB = getattr(
        settings, 'HIDE_USER_TAB', False)


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


def get_manager_email(owner):
    """ owner instanceOf User Model
        return email of user's manager if exist
        else return all managers email
    """
    # Si la fonctionnalité des etablissements est activée
    if USE_ESTABLISHMENT and owner:
        v_estab = owner.owner.establishment.lower()
        # vérifier si le mail du manager (de l'etablissement
        # du propriétaire de la vidéo) est renseigné
        if v_estab in dict(MANAGERS):
            # print('send to ------> ', [dict(MANAGERS)[v_estab]])
            return [dict(MANAGERS)[v_estab]]
    return CONTACT_US_EMAIL


def get_dest_email(owner, video, form_subject, request):
    dest_email = []
    # Soit le owner a été spécifié
    # Soit on le récupere via la video
    # v_owner = instance de User
    v_owner = owner if (
            owner) else getattr(
                    video, 'owner', None)
    # Si ni le owner ni la video a été renseigné
    if not v_owner:
        # Vérifier si l'utilisateur est authentifié
        # le manager de son etablissement sera le dest du mail
        if request.user.is_authenticated():
            return get_manager_email(request.user)
        # Autrement le destinataire du mail sera le(s) manager(s)
        # ou le support dans le cas de Grenoble
        return SUPPORT_EMAIL if (
            USE_SUPPORT_EMAIL) else CONTACT_US_EMAIL

    # Si activation de la fonctionnalité de mail custom
    if CUSTOM_CONTACT_US:
        # vérifier si le sujet du mail est attribué
        # au propriétaire de la vidéo
        if form_subject in USER_CONTACT_EMAIL_CASE:
            dest_email = [v_owner.email]
        else:
            dest_email = get_manager_email(v_owner)
    else:
        # Sinon aucune envie d'utiliser cette fonctionnalité
        # On utilise le fonctionnement de base
        dest_email = [owner.email] if owner else CONTACT_US_EMAIL
    return dest_email


@csrf_protect
def contact_us(request):
    owner = User.objects.get(id=request.GET.get('owner')) if (
        request.GET.get('owner')
        and User.objects.filter(id=request.GET.get('owner')).first()) else None

    video = Video.objects.get(id=request.GET.get('video'),
                              sites=get_current_site(request)) if (
        request.GET.get('video')
        and Video.objects.filter(
            id=request.GET.get('video'),
            sites=get_current_site(request)).first()
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

            dest_email = []
            dest_email = get_dest_email(
                owner,
                video,
                form_subject,
                request
                )

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


def remove_accents(input_str):
    nfkd_form = unicodedata.normalize('NFKD', input_str)
    only_ascii = nfkd_form.encode('ASCII', 'ignore')
    return only_ascii


@login_required(redirect_field_name='referrer')
def user_autocomplete(request):
    if HIDE_USER_TAB:
        return HttpResponseBadRequest()
    if request.is_ajax():
        additional_filters = {
            'video__is_draft': False,
            'owner__sites': get_current_site(request)
        }
        if MENUBAR_HIDE_INACTIVE_OWNERS:
            additional_filters['is_active'] = True
        if MENUBAR_SHOW_STAFF_OWNERS_ONLY:
            additional_filters['is_staff'] = True
        VALUES_LIST = ['username', 'first_name', 'last_name', 'video_count']
        q = remove_accents(request.GET.get('term', '').lower())
        users = User.objects.filter(
          **additional_filters
        ).filter(Q(username__istartswith=q) |
                 Q(last_name__istartswith=q) |
                 Q(first_name__istartswith=q)).distinct().order_by(
            "last_name").annotate(video_count=Count(
                "video", sites=get_current_site(
                    request), distinct=True)).values(*list(VALUES_LIST))

        data = json.dumps(list(users))
    else:
        return HttpResponseBadRequest()
    mimetype = 'application/json'
    return HttpResponse(data, mimetype)
