from ..django.base import POD_VERSION

SPECTACULAR_SETTINGS = {
    'TITLE': 'Pod REST API',
    'DESCRIPTION': 'Video management API (Local Authentication)',
    'VERSION': POD_VERSION,
    'SERVE_INCLUDE_SCHEMA': False,
    'COMPONENT_SPLIT_REQUEST': True,
}