"""Esup-Pod custom PageNumberPagination test cases."""

from django.test import TestCase
from rest_framework.test import APITestCase, APIClient
from rest_framework.test import APIRequestFactory
from rest_framework.request import Request
from rest_framework.exceptions import NotFound
from pod.main.rest_pagination import CustomPagination
from django.contrib.auth.models import User
from rest_framework.authtoken.models import Token


class CustomPaginationTestCase(TestCase):
    """CustomPagination class tests"""

    def setUp(self):
        """Initializing test data"""
        self.factory = APIRequestFactory()
        self.pagination = CustomPagination()

        self.users = [
            User.objects.create_user(username=f"user{i}", email=f"user{i}@test.com")
            for i in range(50)
        ]
        self.queryset = User.objects.all().order_by("id")

    def test_default_page_size(self):
        """Default page size test"""
        request = self.factory.get("/rest/users/")
        request = Request(request)

        paginated = self.pagination.paginate_queryset(self.queryset, request)

        self.assertEqual(len(paginated), 12)  # default page_size

    def test_custom_page_size(self):
        """Custom page_size test"""
        request = self.factory.get("/rest/users/?page_size=25")
        request = Request(request)

        paginated = self.pagination.paginate_queryset(self.queryset, request)

        self.assertEqual(len(paginated), 25)

    def test_max_page_size_limit(self):
        """max_page_size compliance test"""
        request = self.factory.get("/rest/users/?page_size=9999")
        request = Request(request)

        paginated = self.pagination.paginate_queryset(self.queryset, request)

        self.assertLessEqual(len(paginated), 1000)

    def test_get_all_results(self):
        """Getting all results test"""
        request = self.factory.get("/rest/users/?page_size=1000")
        request = Request(request)

        paginated = self.pagination.paginate_queryset(self.queryset, request)

        self.assertEqual(len(paginated), 50)  # All users

    def test_pagination_response_structure(self):
        """Paginated response format test"""
        request = self.factory.get("/rest/users/")
        request = Request(request)

        self.pagination.paginate_queryset(self.queryset, request)

        response = self.pagination.get_paginated_response([])

        # Check the format
        self.assertIn("count", response.data)
        self.assertIn("next", response.data)
        self.assertIn("previous", response.data)
        self.assertIn("results", response.data)

        self.assertEqual(response.data["count"], 50)

    def test_second_page(self):
        """Second page browsing test"""
        request = self.factory.get("/rest/users/?page=2")
        request = Request(request)

        paginated = self.pagination.paginate_queryset(self.queryset, request)

        self.assertEqual(len(paginated), 12)
        self.assertEqual(paginated[0].id, self.users[12].id)

    def test_invalid_page_number(self):
        """Invalid page number test"""
        request = self.factory.get("/rest/users/?page=999")
        request = Request(request)

        with self.assertRaises(NotFound):
            self.pagination.paginate_queryset(self.queryset, request)

    def test_page_size_zero(self):
        """Value page_size=0 test"""
        request = self.factory.get("/rest/users/?page_size=0")
        request = Request(request)

        paginated = self.pagination.paginate_queryset(self.queryset, request)

        self.assertGreater(len(paginated), 0)

    def test_negative_page_size(self):
        """Negative page_size test"""
        request = self.factory.get("/rest/users/?page_size=-10")
        request = Request(request)

        paginated = self.pagination.paginate_queryset(self.queryset, request)

        self.assertEqual(len(paginated), 12)


class CustomPaginationIntegrationTestCase(APITestCase):
    """Integration tests for CustomPagination class using the API"""

    def setUp(self):
        """Initializing test data"""
        self.client = APIClient()

        for i in range(30):
            User.objects.create_user(username=f"user{i}", email=f"user{i}@test.com")
        self.admin = User.objects.create(
            first_name="pod",
            last_name="Admin",
            username="admin",
            password="admin1234admin",
            is_staff=True,
            is_superuser=True,
        )
        self.token = Token.objects.create(user=self.admin)
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.token.key}")

    def test_api_pagination_default(self):
        """Pagination test via the real API"""

        response = self.client.get("/rest/users/")

        self.assertEqual(response.status_code, 200)
        self.assertIn("count", response.json())
        self.assertIn("results", response.json())
        self.assertEqual(len(response.json()["results"]), 12)

    def test_api_custom_page_size(self):
        """Custom page_size test via the real API"""

        response = self.client.get("/rest/users/?page_size=20")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()["results"]), 20)
