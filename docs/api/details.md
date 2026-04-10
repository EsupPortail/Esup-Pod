# API: Technical Details & Documentation

How to document your code so it appears in Swagger/OpenAPI.

## Principle

Documentation lives in the code. By using `drf-spectacular` decorators, you keep the documentation synchronized with the implementation.

## Documenting a ViewSet

Use the `@extend_schema` decorator from `drf_spectacular.utils`.

### 1. Grouping Endpoints (Tags)

Add this decorator above the ViewSet class to organize its methods into logical groups.

```python
from drf_spectacular.utils import extend_schema
@extend_schema(tags=['Video Management'])  # Creates a "Video Management" group
class VideoViewSet(viewsets.ModelViewSet):
    queryset = Video.objects.all()
    serializer_class = VideoSerializer
```

### 2. Detailing a Specific Method

Add this decorator to the specific method (create, list, retrieve, etc.) to document that endpoint.

```python
@extend_schema(
    summary="Create a video",
    description="Uploads a video file and creates the associated metadata entry.",
    responses={
        201: VideoSerializer,  # Success
        400: OpenApiTypes.OBJECT,  # Validation error
    },
    examples=[
        OpenApiExample(
            'Valid Example',
            value={'title': 'My Holiday Video'}
        )
    ]
)
def create(self, request):
    # Implementation...
    pass
```

### 3. Parameters & Query Strings

Document request parameters with `@extend_schema` and `OpenApiParameter`:

```python
from drf_spectacular.utils import extend_schema, OpenApiParameter
from drf_spectacular.types import OpenApiTypes
@extend_schema(
    parameters=[
        OpenApiParameter(
            name='search',
            description='Search by video title',
            required=False,
            type=OpenApiTypes.STR,
        ),
        OpenApiParameter(
            name='ordering',
            description='Order by field (e.g., -created_at)',
            required=False,
            type=OpenApiTypes.STR,
        ),
    ]
)
def list(self, request):
    # Implementation...
    pass
```

## Viewing Documentation

The API documentation is auto-generated and available at:

- **Swagger UI** (interactive): `http://localhost:8000/api/docs/`
- **ReDoc** (readable): `http://localhost:8000/api/redoc/`
- **Raw Schema** (YAML): `http://localhost:8000/api/schema/`
- **Raw Schema** (JSON): `http://localhost:8000/api/schema/?format=json`

## Best Practices

1. **Keep descriptions short**: Use `summary` for titles, `description` for details.
2. **Document all response codes**: Include success (200, 201) and error (400, 404) responses.
3. **Use examples**: Help developers understand expected payloads.
4. **Match the code**: Update docs when you change implementation.
5. **Group logically**: Use consistent tags across your API.

## Further Reading

- [drf-spectacular Documentation](https://drf-spectacular.readthedocs.io/)
- [OpenAPI 3.0 Specification](https://spec.openapis.org/oas/v3.0.3)
- ⬅️ **[Back to Overview](README.md)**
- ⬅️ **[Back to Index](../README.md)**
