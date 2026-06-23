"""
Esup-Pod - Authentication application FilterSets.

Provides generic, reusable FilterSet classes for User, Owner, and AccessGroup models.
"""

import django_filters
from django_filters import rest_framework as filters
from django.utils.translation import gettext_lazy as _
from django.contrib.auth import get_user_model

from src.apps.authentication.models import AccessGroup

User = get_user_model()


class MultiValueCharFilter(filters.BaseInFilter, filters.CharFilter):
    """
    Allows filtering by multiple values for a single CharField.
    Usage: ?username=alice&username=bob
    """

    pass


class UserFilterSet(django_filters.FilterSet):
    """
    FilterSet for the User model.
    """

    id = django_filters.BaseInFilter(
        field_name="id",
        label=_("User ID(s) — multi-value supported"),
    )
    username = MultiValueCharFilter(
        field_name="username",
        lookup_expr="in",
        label=_("Username(s) — multi-value supported"),
    )
    email = MultiValueCharFilter(
        field_name="email",
        lookup_expr="in",
        label=_("Email(s) — multi-value supported"),
    )
    is_staff = django_filters.BooleanFilter(field_name="is_staff")
    is_superuser = django_filters.BooleanFilter(field_name="is_superuser")

    class Meta:
        """UserFilterSet metadata."""

        model = User
        fields = [
            "id",
            "username",
            "email",
            "is_staff",
            "is_superuser",
        ]


class AccessGroupFilterSet(django_filters.FilterSet):
    """
    FilterSet for the AccessGroup model.
    """

    id = django_filters.BaseInFilter(
        field_name="id",
        label=_("Group ID(s) — multi-value supported"),
    )
    code_name = MultiValueCharFilter(
        field_name="code_name",
        lookup_expr="in",
        label=_("Code name(s) — multi-value supported"),
    )
    display_name = filters.CharFilter(
        field_name="display_name",
        lookup_expr="icontains",
        label=_("Display name contains"),
    )

    class Meta:
        """AccessGroupFilterSet metadata."""

        model = AccessGroup
        fields = ["id", "code_name", "display_name"]
