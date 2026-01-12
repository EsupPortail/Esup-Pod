# 👨‍💻 API Developer Guide

How to document your code so it appears in Swagger.

## Principle
Documentation lives in the code. By using `drf-spectacular` decorators, you keep the documentation synchronized with the implementation.

## Documenting a View

Use the `@extend_schema` decorator.

### 1. Grouping Endpoints (Tags)

Add this above the ViewSet class to group its methods.

```python
from drf_spectacular.utils import extend_schema

@extend_schema(tags=['Video Management'])  # Creates a "Video Management" group
class VideoViewSet(viewsets.ModelViewSet):
    ...
```

### 2. Detailing a Method

Add this to the specific method (create, list, etc.).

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
    ...
```

## Best Practices

*   **Error Codes**: Always document error cases (400, 403, 404). The frontend needs to know what to expect.
*   **Examples**: For complex requests (POST/PUT), provide a valid JSON example.
