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
        self.selected_facets = [
            "type.slug.raw:value1",
            "tags.slug.raw:value2",
            "disciplines.slug:value3",
        ]

    def test_get_filter_search(self):
        start_date = datetime.now()
        end_date = start_date + timedelta(days=10)

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
        actual = get_filter_search([], start_date, end_date)
        self.assertEqual(actual, expected)

        expected = [
            *[
                {"term": {facet.split(":")[0]: facet.split(":")[1]}}
                for facet in self.selected_facets
            ],
            *expected,
        ]
        actual = get_filter_search(self.selected_facets, start_date, end_date)
        self.assertEqual(actual, expected)

    def test_get_remove_selected_facet_link(self):
        request_factory = RequestFactory()
        request = request_factory.get(
            "/search/?q=video",
            {
                "q": "video",
                "selected_facets": self.selected_facets,
            },
        )

        actual = get_remove_selected_facet_link(request, self.selected_facets)

        msg_title = "Remove this filter"
        expected = []
        for index, facet in enumerate(self.selected_facets):
            link = request.get_full_path().replace(
                f"&selected_facets={facet}", ""
            )
            expected.append(
                '<a href="%s" title="%s">%s</a>'
                % (link, msg_title, facet.split(":")[1]),
            )

        self.assertEqual(actual, expected)
