from datetime import datetime, timedelta

from django.test import TestCase

from pod.video.views import get_filter_search


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
                            start_date.year,
                            start_date.month,
                            start_date.day,
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
