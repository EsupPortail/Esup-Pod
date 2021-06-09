from datetime import datetime, timedelta

from django.test import TestCase
from django.test.client import RequestFactory

from pod.video_search.views import (
    get_filter_search,
    get_remove_selected_facet_link,
)


class VideoSearchTest(TestCase):
    fixtures = [
        "initial_data.json",
    ]

    def setUp(self):
        pass

    def test_get_filter_search(self):
        start_date = datetime.now()
        end_date = start_date + timedelta(days=10)

        selected_facets = []
        expected = [
            {
                "range": {
                    "date_added": {
                        "gte": "%04d-%02d-%02d"
                        % (
                            start_date.year,
                            start_date.month,
                            start_date.day,
                        ),
                        "lte": "%04d-%02d-%02d"
                        % (
                            end_date.year,
                            end_date.month,
                            end_date.day,
                        ),
                    }
                }
            }
        ]
        actual = get_filter_search(selected_facets, start_date, end_date)
        self.assertEqual(actual, expected)

        selected_facets = ["term1:value1", "term2:value2"]
        expected = [
            {"term": {"term1": "value1"}},
            {"term": {"term2": "value2"}},
            *expected,
        ]
        actual = get_filter_search(selected_facets, start_date, end_date)
        self.assertEqual(actual, expected)

    def test_get_remove_selected_facet_link(self):
        request_factory = RequestFactory()
        request = request_factory.get(
            "/search/?q=video",
            {
                "q": "video",
                "selected_facets": ["term1:value1", "term2:value2"],
            },
        )
        selected_facets = ["term1:value1", "term2:value2"]

        actual = get_remove_selected_facet_link(request, selected_facets)

        link1 = request.get_full_path().replace(
            "&selected_facets=term1:value1", ""
        )
        link2 = request.get_full_path().replace(
            "&selected_facets=term2:value2", ""
        )
        msg_title = "Remove this filter"
        expected = [
            '<a href="%s" title="%s">%s</a>' % (link1, msg_title, "value1"),
            '<a href="%s" title="%s">%s</a>' % (link2, msg_title, "value2"),
        ]

        self.assertEqual(actual, expected)
