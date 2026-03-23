"""
Esup-Pod - Utilities for configuration management.
Provides a Pydantic settings source that reads from Django settings.
"""

from typing import Any, Tuple

from django.conf import settings
from pydantic.fields import FieldInfo
from pydantic_settings import (
    PydanticBaseSettingsSource,
)


class DjangoSettingsSource(PydanticBaseSettingsSource):
    """
    A Pydantic settings source that reads configuration from Django settings.

    It allows developers to override Pydantic settings by defining variables
    in their Django settings files (e.g. src/config/settings/{app_name}.py).
    """

    def get_field_value(self, field: FieldInfo, field_name: str) -> Tuple[Any, str, bool]:
        simple_setting_name = field_name.upper()
        if hasattr(settings, simple_setting_name):
            return getattr(settings, simple_setting_name), field_name, False

        env_prefix = self.config.get("env_prefix", "")
        if env_prefix:
            prefixed_setting_name = (env_prefix + field_name).upper()
            if hasattr(settings, prefixed_setting_name):
                return getattr(settings, prefixed_setting_name), field_name, False

        return None, field_name, False

    def __call__(self) -> dict[str, Any]:
        """
        Build the dictionary of settings found in Django settings.
        """
        d: dict[str, Any] = {}
        for field_name, field in self.settings_cls.model_fields.items():
            value, _, is_complex = self.get_field_value(field, field_name)
            if value is not None:
                d[field_name] = value
        return d
