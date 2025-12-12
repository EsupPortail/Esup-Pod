# 📘 API Documentation Guide (OpenAPI / Swagger)

This project uses drf-spectacular to automatically generate interactive documentation compliant with the OpenAPI 3.0 specification.

Unlike older methods (hand-written doc), here the code is the documentation. By correctly annotating your Django Views and Serializers, the documentation updates automatically.

## 🚀 1. Accessing the Documentation

Once the server is launched, three interfaces are available: 
| Interface | URL | Usage | 
| ------------- |:-------------:| ------------- | 
| Swagger UI | URL/api/docs/ | For Developers. Interactive interface allowing requests (GET, POST, DELETE...) to be tested directly from the browser. | 
| ReDoc | URL/api/redoc/ | For Readers. A clean, hierarchical, and modern presentation of all the code. | 
| YAML Schema | URL/api/schema/ | For Machines. The raw specification file. Useful for automatically generating other codes. |

## 👨‍💻 2. Developer Guide: How to document?

A. Documenting a View (Endpoint)

This is the most important step. We use the @extend_schema decorator on the ViewSet methods.

To place before the class in views.py:
```py
@extend_schema(tags=['Video Management'])  # 1. Groups all endpoints under this Tag
```

To place on each endpoint in views.py:
```py
@extend_schema(
        summary="test",
        parameters=[
            OpenApiParameter(
                name='category', 
                description='Filter', 
                required=False, 
                type=str
            )],
        examples=[
            OpenApiExample(
                'Simple Example',
                value={
                    'title': 'test',
                    'url': 'localhost',
                    'description': 'test'
                }
            )
        ],
        responses={
            404: {"description": "None found"}
        }
    )
```

## 🚦 3. Best Practices
Handle errors: Always document error cases (400, 403, 404) in the responses section. The front-end must know what to expect if it fails.

Use examples: For complex endpoints (POST/PUT), use OpenApiExample to show valid JSON.