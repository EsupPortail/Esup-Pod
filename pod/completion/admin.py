"""Admin pages for Esup-Pod Completion items."""
from pyexpat import model
from django.conf import settings
from django.contrib import admin
from django.utils.translation import ugettext_lazy as _
from pod.completion.models import Contributor
from pod.completion.models import Document
from pod.completion.models import Overlay
from pod.completion.models import Track
from pod.completion.models import EnrichModelQueue
from pod.completion.forms import DocumentAdminForm
from pod.completion.forms import TrackAdminForm
from django.contrib.sites.shortcuts import get_current_site
from django.contrib.sites.models import Site
from pod.video.models import Video
from pod.custom.settings_local import MODEL_COMPILE_DIR

import subprocess
import webvtt
import threading
import os
import shutil

FILEPICKER = False
if getattr(settings, "USE_PODFILE", False):
    FILEPICKER = True

DEBUG = getattr(settings, "DEBUG", True)
TRANSCRIPTION_TYPE = getattr(settings, "TRANSCRIPTION_TYPE", "DEEPSPEECH")
MODEL_PARAM = getattr(settings, "MODEL_PARAM", {})

class ContributorInline(admin.TabularInline):
    model = Contributor
    readonly_fields = (
        "video",
        "name",
        "email_address",
        "role",
        "weblink",
    )
    extra = 0

    def has_add_permission(self, request, obj=None):
        return False


class ContributorAdmin(admin.ModelAdmin):

    list_display = ('name', 'role', 'video',)
    list_display_links = ('name',)
    list_filter = ('role',)
    search_fields = ['id', 'name', 'role', 'video__title']
    autocomplete_fields = ['video']

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if (db_field.name) == "video":
            kwargs["queryset"] = Video.objects.filter(sites=Site.objects.get_current())
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    class Media:
        css = {"all": ("css/pod.css",)}

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if not request.user.is_superuser:
            qs = qs.filter(video__sites=get_current_site(request))
        return qs


admin.site.register(Contributor, ContributorAdmin)


class DocumentInline(admin.TabularInline):
    model = Document
    readonly_fields = (
        "video",
        "document",
    )
    extra = 0

    def has_add_permission(self, request, obj=None):
        return False


class DocumentAdmin(admin.ModelAdmin):

    if FILEPICKER:
        form = DocumentAdminForm
    list_display = ('document', 'video',)
    list_display_links = ('document',)
    search_fields = ['id', 'document__name', 'video__title']
    autocomplete_fields = ['video']

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if not request.user.is_superuser:
            qs = qs.filter(video__sites=get_current_site(request))
        return qs

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if (db_field.name) == "video":
            kwargs["queryset"] = Video.objects.filter(sites=Site.objects.get_current())
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    class Media:
        USE_THEME = getattr(settings, "USE_THEME", "default")
        css = {
            "all": (
                "bootstrap-4/css/bootstrap-%s.min.css" % USE_THEME,
                "bootstrap-4/css/bootstrap-grid.css",
                "css/pod.css",
            )
        }
        js = (
            "podfile/js/filewidget.js",
            "js/main.js",
            "feather-icons/feather.min.js",
            "bootstrap-4/js/bootstrap.min.js",
        )


admin.site.register(Document, DocumentAdmin)


class TrackInline(admin.TabularInline):
    model = Track
    readonly_fields = (
        "video",
        "kind",
        "lang",
        "src",
        "enrich_ready",
    )
    extra = 0

    def has_add_permission(self, request, obj=None):
        return False

class EnrichModelQueueAdmin(admin.ModelAdmin):
    list_display = ('title', 'in_treatment',)
    list_filter = ('in_treatment',)

admin.site.register(EnrichModelQueue, EnrichModelQueueAdmin)

class TrackAdmin(admin.ModelAdmin):
    
    @admin.action(description=_('Enrich with selected subtitles'))
    def enrich_model(modeladmin, request, queryset):
        def debug(text):
            if(DEBUG):
                print(text)
                
        def check_if_treatment_in_progress() -> bool:
            return EnrichModelQueue.objects.filter(in_treatment=True).exists()
    
        def write_into_kaldi_file(enrichModelQueue: EnrichModelQueue):
            with open(MODEL_COMPILE_DIR+"/"+enrichModelQueue.lang+'/db/extra.txt', 'w') as f:
                f.write(enrichModelQueue.text)
            subprocess.call(['docker', 'run', '-v', MODEL_COMPILE_DIR+':/kaldi/compile-model', '-it', 'kaldi', enrichModelQueue.lang])
            
        def copy_result_into_current_model(enrichModelQueue: EnrichModelQueue):
            from_path: str = MODEL_COMPILE_DIR+"/"+enrichModelQueue.lang+'/exp/chain/tdnn/graph'
            to_path: str = MODEL_PARAM[enrichModelQueue.model_type][enrichModelQueue.lang]["model"]+'/graph'
            if os.path.exists(to_path):
                shutil.rmtree(to_path)
            shutil.copytree(from_path, to_path)
            
            from_path: str = MODEL_COMPILE_DIR+"/"+enrichModelQueue.lang+'/data/lang_test_rescore'
            to_path: str = MODEL_PARAM[enrichModelQueue.model_type][enrichModelQueue.lang]["model"]+'/rescore/'
            if os.path.isfile(from_path+'/G.fst') and os.path.isfile(from_path+'/G.carpa'):
                shutil.copy(from_path+'/G.fst', to_path)
                shutil.copy(from_path+'/G.carpa', to_path)
                
            from_path: str = MODEL_COMPILE_DIR+"/"+enrichModelQueue.lang+'/exp/rnnlm_out'
            to_path: str = MODEL_PARAM[enrichModelQueue.model_type][enrichModelQueue.lang]["model"]+'/rnnlm/'
            if os.path.exists(from_path):
                shutil.copy(from_path, to_path)
                
        def enrich_kaldi_model_launch():
            debug("enrich_kaldi_model")
            enrichModelQueue = EnrichModelQueue.objects.filter(model_type="VOSK").first()
            if(enrichModelQueue != None):
                enrichModelQueue.in_treatment = True
                enrichModelQueue.save()
                debug("start subprocess")
                write_into_kaldi_file(enrichModelQueue)
                debug("finish subprocess")
                debug("start copy result")
                copy_result_into_current_model(enrichModelQueue)
                debug("finish copy result")
                enrichModelQueue.delete()
                enrich_kaldi_model_launch()
                return
            else:
                debug("All queues have been completed !")
                return
            
        text = ""
        title = ""
        for query in list(queryset.all()):
            if(title != ""):
                title += " /-/ "
            title += query.video.title
            file = query.src.file
            for caption in webvtt.read(file.path):
                text += caption.text+" \n"
            query.enrich_ready = False
            query.save()
            
        EnrichModelQueue(
            title = title,
            text = text,
            lang = query.lang,
            model_type = TRANSCRIPTION_TYPE
        ).save()
        
        if(not check_if_treatment_in_progress()):
            if(TRANSCRIPTION_TYPE == "VOSK"):
                t = threading.Thread(target=enrich_kaldi_model_launch, args=[])
                t.setDaemon(True)
                t.start()
            
    if FILEPICKER:
        form = TrackAdminForm
    list_display = ('src', 'kind', 'video', 'enrich_ready',)
    list_display_links = ('src',)
    list_filter = ('kind', 'enrich_ready',)
    search_fields = ['id', 'src__name', 'kind', 'video__title', ]
    autocomplete_fields = ['video']
    actions = [enrich_model]
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if not request.user.is_superuser:
            qs = qs.filter(video__sites=get_current_site(request))
        return qs

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if (db_field.name) == "video":
            kwargs["queryset"] = Video.objects.filter(sites=Site.objects.get_current())
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    class Media:
        css = {
            "all": (
                "bootstrap-4/css/bootstrap.min.css",
                "bootstrap-4/css/bootstrap-grid.css",
                "css/pod.css",
            )
        }
        js = (
            "js/main.js",
            "podfile/js/filewidget.js",
            "feather-icons/feather.min.js",
            "bootstrap-4/js/bootstrap.min.js",
        )


admin.site.register(Track, TrackAdmin)


class OverlayInline(admin.TabularInline):
    model = Overlay
    readonly_fields = (
        "video",
        "title",
        "time_start",
        "time_end",
        "content",
        "position",
        "background",
    )
    exclude = ("slug",)
    extra = 0

    def has_add_permission(self, request, obj=None):
        return False


class OverlayAdmin(admin.ModelAdmin):

    list_display = ('title', 'video',)
    list_display_links = ('title',)
    search_fields = ['id', 'title', 'video__title']
    autocomplete_fields = ['video']

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if not request.user.is_superuser:
            qs = qs.filter(video__sites=get_current_site(request))
        return qs

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if (db_field.name) == "video":
            kwargs["queryset"] = Video.objects.filter(sites=Site.objects.get_current())
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    class Media:
        css = {"all": ("css/pod.css",)}


admin.site.register(Overlay, OverlayAdmin)
