from django.shortcuts import render
from elasticsearch import Elasticsearch
from pod.video_search.forms import SearchForm
from django.conf import settings
from pod.video.models import Video
from django.utils.translation import ugettext_lazy as _

# import json

ES_URL = getattr(settings, 'ES_URL', ['http://pod-dev.grenet.fr/'])

# Create your views here.


def get_filter_search(selected_facets, start_date, end_date):
    filter_search = []
    for facet in selected_facets:
        if ":" in facet:
            term = facet.split(":")[0]
            value = facet.split(":")[1]
            filter_search.append({
                "term": {
                    "%s" % term: "%s" % value
                }
            })

    if start_date or end_date:
        filter_date_search = {}
        filter_date_search["range"] = {"date_added": {}}
        if start_date:
            filter_date_search["range"]["date_added"][
                "gte"] = "%04d-%02d-%02d" % (start_date.year,
                                             start_date.month,
                                             start_date.day)
        if end_date:
            filter_date_search["range"]["date_added"][
                "lte"] = "%04d-%02d-%02d" % (end_date.year,
                                             end_date.month,
                                             end_date.day)

        filter_search.append(filter_date_search)
    return filter_search


def get_remove_selected_facet_link(request, selected_facets):
    remove_selected_facet = ""
    for facet in selected_facets:
        if ":" in facet:
            term = facet.split(":")[0]
            value = facet.split(":")[1]
            link = request.get_full_path().replace(
                "&selected_facets=%s:%s" % (term, value), "")
            link = request.get_full_path().replace(
                "?selected_facets=%s:%s" % (term, value), "")
            msg_title = _('Remove selection')
            remove_selected_facet += (
                '&nbsp;<a href="%s" title="%s">&times;%s</a>&nbsp;' % (
                    link, msg_title, value))
    return remove_selected_facet


def get_result_aggregations(result, selected_facets):
    for facet in selected_facets:
        if ":" in facet:
            term = facet.split(":")[0]
            agg_term = term.replace(".raw", "")
            if result["aggregations"].get(agg_term):
                del result["aggregations"][agg_term]
            else:
                if agg_term == "type.slug":
                    del result["aggregations"]["type_title"]
                if agg_term == "tags.slug":
                    del result["aggregations"]["tags_name"]
                if agg_term == "disciplines.slug":
                    del result["aggregations"]["disciplines_title"]
    return result["aggregations"]


def search_videos(request):
    es = Elasticsearch(ES_URL)
    aggsAttrs = ['owner_full_name', 'type.title',
                 'disciplines.title', 'tags.name', 'channels.title', 'video.cursus']

    # SEARCH FORM
    search_word = ""
    start_date = None
    end_date = None
    searchForm = SearchForm(request.GET)
    if searchForm.is_valid():
        search_word = searchForm.cleaned_data['q']
        start_date = searchForm.cleaned_data['start_date']
        end_date = searchForm.cleaned_data['end_date']

    # request parameters
    selected_facets = request.GET.getlist(
        'selected_facets') if request.GET.getlist('selected_facets') else []

    page = request.GET.get('page', '0')
    page = int(page) if page.isdigit() else 0
    size = 12

    search_from = page * size

    # Filter query
    filter_search = get_filter_search(selected_facets, start_date, end_date)

    # Query
    query = {"match_all": {}}
    if search_word != "":
        query = {
            "multi_match": {
                "query":    "%s" % search_word,
                "operator": "and",
                "fields": [
                    "_id",
                    "title^1.1",
                    "owner^0.9",
                    "owner_full_name^0.9",
                    "description^0.6",
                    "tags.name^1",
                    "contributors^0.6",
                    "chapters.title^0.5",
                    "type.title^0.6",
                    "disciplines.title^0.6",
                    "channels.title^0.6"
                ]
            }
        }

    # bodysearch
    bodysearch = {
        "from": search_from,
        "size": size,
        "query": {},
        "aggs": {},
        "highlight": {
            "pre_tags": ["<mark>"],
            "post_tags": ["</mark>"],
            "fields": {"title": {"force_source": "true"}}
        }
    }

    bodysearch["query"] = {
        "function_score": {
            "query": {},
            "functions": [
                {
                    "gauss": {
                        "date_added": {
                            "scale": "10d",
                            "offset": "5d",
                            "decay": 0.5
                        }
                    }
                }
            ]
        }
    }

    if filter_search != {}:
        bodysearch["query"]["function_score"]["query"] = {"bool": {}}
        bodysearch["query"]["function_score"][
            "query"]["bool"]["must"] = query
        bodysearch["query"]["function_score"]["query"][
            "bool"]["filter"] = filter_search
    else:
        bodysearch["query"]["function_score"]["query"] = query

    for attr in aggsAttrs:
        bodysearch["aggs"][attr.replace(".", "_")] = {
            "terms": {"field": attr + ".raw",
                      "size": 5,
                      "order": {"_count": "desc"}}}

    # add cursus and main_lang 'cursus', 'main_lang',
    bodysearch["aggs"]['cursus'] = {
        "terms": {"field": "cursus", "size": 5, "order": {"_count": "desc"}}}
    bodysearch["aggs"]['main_lang'] = {
        "terms": {"field": "main_lang",
                  "size": 5,
                  "order": {"_count": "desc"}}}

    # if settings.DEBUG:
    #    print(json.dumps(bodysearch, indent=4))

    result = es.search(index="pod", body=bodysearch)

    # if settings.DEBUG:
    #    print(json.dumps(result, indent=4))

    remove_selected_facet = get_remove_selected_facet_link(
        request, selected_facets)
    aggregations = get_result_aggregations(result, selected_facets)

    full_path = request.get_full_path().replace(
        "?page=%s" % page, "").replace("&page=%s" % page, "")

    list_videos_id = [hit["_id"] for hit in result["hits"]["hits"]]
    videos = Video.objects.filter(id__in=list_videos_id)
    num_result = result["hits"]["total"]
    videos.has_next = ((page + 1) * 12) < num_result
    videos.next_page_number = page + 1

    if request.is_ajax():
        return render(
            request, 'videos/video_list.html',
            {'videos': videos, "full_path": full_path})

    return render(request, "search/search.html",
                  {"full_path": full_path,
                   "videos": videos,
                   "num_result": num_result,
                   "aggregations": aggregations,
                   "form": searchForm,
                   "remove_selected_facet": remove_selected_facet})
