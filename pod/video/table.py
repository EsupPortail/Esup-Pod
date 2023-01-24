import django_tables2 as tables
from django_tables2.export.views import ExportMixin
from django.utils.translation import ugettext_lazy as _
from django.utils.text import format_lazy

class Stats_table(ExportMixin, tables.Table):
    #template_name = "django_tables2/semantic.html"

    export_formats = ['csv', 'xlsx', 'ods']

    video_id = tables.Column(verbose_name="Id", order_by="id", orderable=True)
    title = tables.Column(verbose_name=_("Title"), orderable=False)
    day = tables.Column(verbose_name=_("Views during the day"), orderable=True)
    month = tables.Column(verbose_name=_("Views during the month"), orderable=True)
    year = tables.Column(verbose_name=_("Views during the year"), orderable=True)
    since_created = tables.Column(verbose_name=_("Total views from creation"), orderable=True)
    detail_link = tables.TemplateColumn(template_code=format_lazy('<button onclick="window.location.href={};">{}</button>', '\'{% url "video_stats_view" id=record.video_id %}\'', _("See detail")),
        verbose_name=_("Detail"), orderable=False, exclude_from_export=True)

