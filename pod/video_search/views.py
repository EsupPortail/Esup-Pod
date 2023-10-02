"""Pod video_search views."""

from django.shortcuts import render
from elasticsearch import Elasticsearch
from pod.video_search.forms import SearchForm
from django.conf import settings
from django.contrib import messages
from pod.video.models import Video
from django.utils.translation import ugettext_lazy as _
from django.utils.html import strip_tags

# import json

ES_URL = getattr(settings, "ES_URL", ["http://127.0.0.1:9200/"])
ES_INDEX = getattr(settings, "ES_INDEX", "pod")
ES_TIMEOUT = getattr(settings, "ES_TIMEOUT", 30)
ES_MAX_RETRIES = getattr(settings, "ES_MAX_RETRIES", 10)
ES_VERSION = getattr(settings, "ES_VERSION", 6)


def get_filter_search(selected_facets, start_date, end_date):
    """Return a list of search filters."""
    filter_search = []
    for facet in selected_facets:
        if ":" in facet:
            term = facet.split(":")[0]
            value = facet.split(":")[1]
            filter_search.append({"term": {"%s" % term: "%s" % value}})

    if start_date or end_date:
        filter_date_search = {}
        filter_date_search["range"] = {"date_added": {}}
        if start_date:
            filter_date_search["range"]["date_added"]["gte"] = "%04d-%02d-%02d" % (
                start_date.year,
                start_date.month,
                start_date.day,
            )
        if end_date:
            filter_date_search["range"]["date_added"]["lte"] = "%04d-%02d-%02d" % (
                end_date.year,
                end_date.month,
                end_date.day,
            )

        filter_search.append(filter_date_search)
    return filter_search


def get_remove_selected_facet_link(request, selected_facets):
    """Return list of links to remove active search filters."""
    remove_selected_facet = []
    for facet in selected_facets:
        if ":" in facet:
            term = facet.split(":")[0]
            value = strip_tags(facet.split(":")[1])
            link = request.get_full_path().replace(
                "&selected_facets=%s:%s" % (term, value), ""
            )
            link = link.replace("?selected_facets=%s:%s&" % (term, value), "?")
            link = link.replace("?selected_facets=%s:%s" % (term, value), "")
            msg_title = _("Remove this filter")
            remove_selected_facet.append(
                '<a href="%s" title="%s">%s</a>' % (link, msg_title, value)
            )
    return remove_selected_facet


def get_result_aggregations(result, selected_facets):
    """Return aggregation results, without selected_facets."""
    for facet in selected_facets:
        if ":" in facet:
            term = facet.split(":")[0]
            agg_term = term.replace(".raw", "")
            if agg_term == "type.slug":
                agg_term = "type_title"
            elif agg_term == "tags.slug":
                agg_term = "tags_name"
            elif agg_term == "disciplines.slug":
                agg_term = "disciplines_title"

            if result["aggregations"].get(agg_term):
                del result["aggregations"][agg_term]

    return result["aggregations"]


def get_search_page(request):
    """Return page number to start search from Elasticsearch."""
    page = request.GET.get("page", "0")
    page = int(page) if page.isdigit() else 0
    if page > 500:
        page = 500
        messages.warning(request, _("Sorry, video search is limited to 500 pages max."))

    return page


def search_videos(request):
    """Send a search request to ES."""
    es = Elasticsearch(
        ES_URL,
        timeout=ES_TIMEOUT,
        max_retries=ES_MAX_RETRIES,
        retry_on_timeout=True,
    )
    aggsAttrs = [
        "owner_full_name",
        "type.title",
        "disciplines.title",
        "tags.name",
        "channels.title",
    ]

    # SEARCH FORM
    search_word = ""
    start_date = None
    end_date = None
    searchForm = SearchForm(request.GET)
    if searchForm.is_valid():
        search_word = searchForm.cleaned_data["q"]
        start_date = searchForm.cleaned_data["start_date"]
        end_date = searchForm.cleaned_data["end_date"]

    # request parameters
    selected_facets = (
        request.GET.getlist("selected_facets")
        if request.GET.getlist("selected_facets")
        else []
    )

    page = get_search_page(request)
    size = 12
    search_from = page * size

    # Filter query
    filter_search = get_filter_search(selected_facets, start_date, end_date)

    # Query
    query = {"match_all": {}}
    if search_word != "":
        query = {
            "multi_match": {
                "query": "%s" % search_word,
                "operator": "and",
                "fields": [
                    "_id",
                    "title^1.1",
                    "owner^0.9",
                    "owner_full_name^0.9",
                    "description^0.6",
                    "tags.name^1",
                    "type.title^0.6",
                    "disciplines.title^0.6",
                    "channels.title^0.6",
                    "themes.title^0.5",
                    "contributors^0.6",
                    "chapters.title^0.5",
                    "overlays.title^0.5",
                ],
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
            "fields": {"title": {"force_source": "true"}},
        },
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
                            "decay": 0.5,
                        }
                    }
                }
            ],
        }
    }

    if filter_search != {}:
        bodysearch["query"]["function_score"]["query"] = {"bool": {}}
        bodysearch["query"]["function_score"]["query"]["bool"]["must"] = query
        bodysearch["query"]["function_score"]["query"]["bool"]["filter"] = filter_search
    else:
        bodysearch["query"]["function_score"]["query"] = query

    for attr in aggsAttrs:
        bodysearch["aggs"][attr.replace(".", "_")] = {
            "terms": {
                "field": attr + ".raw",
                "size": 5,
                "order": {"_count": "desc"},
            }
        }

    # add cursus and main_lang 'cursus', 'main_lang',
    bodysearch["aggs"]["cursus"] = {
        "terms": {"field": "cursus", "size": 5, "order": {"_count": "desc"}}
    }
    bodysearch["aggs"]["main_lang"] = {
        "terms": {"field": "main_lang", "size": 5, "order": {"_count": "desc"}}
    }

    # if settings.DEBUG:
    #    print(json.dumps(bodysearch, indent=4))

    result = es.search(index=ES_INDEX, body=bodysearch)

    # if settings.DEBUG:
    #    print(json.dumps(result, indent=4))

    remove_selected_facet = get_remove_selected_facet_link(request, selected_facets)
    aggregations = get_result_aggregations(result, selected_facets)

    full_path = (
        request.get_full_path()
        .replace("?page=%s" % page, "")
        .replace("&page=%s" % page, "")
    )

    list_videos_id = [hit["_id"] for hit in result["hits"]["hits"]]
    videos = Video.objects.filter(id__in=list_videos_id)
    num_result = 0
    if ES_VERSION in [7, 8]:
        num_result = result["hits"]["total"]["value"]
    else:
        num_result = result["hits"]["total"]
    videos.has_next = ((page + 1) * size) < num_result
    videos.next_page_number = page + 1

    if request.is_ajax():
        return render(
            request,
            "videos/video_list.html",
            {"videos": videos, "full_path": full_path},
        )

    return render(
        request,
        "search/search.html",
        {
            "full_path": full_path,
            "videos": videos,
            "num_result": num_result,
            "aggregations": aggregations,
            "form": searchForm,
            "remove_selected_facet": remove_selected_facet,
            "page_title": _("Search results"),
        },
    )
