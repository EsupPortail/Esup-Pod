# 🛠 API & Swagger

The Pod V5 API is automatically documented according to the **OpenAPI 3.0** specification using the `drf-spectacular` library.

## Interactive Documentation

We provide two interfaces to explore the API:

*   **[Swagger UI](http://localhost:8000/api/docs/)** (`/api/docs/`): Intended for developers. Allows you to test requests (GET, POST, etc.) directly from the browser.
*   **[ReDoc](http://localhost:8000/api/redoc/)** (`/api/redoc/`): Intended for reading. A modern and clean interface listing all endpoints hierarchically.

## Raw Schema

For automation needs (API client generation, etc.), the raw schema is available:
*   YAML format: `/api/schema/`
*   JSON format: `/api/schema/?format=json`

## Further Reading

*   ➡️ **[Technical Details & Configuration](guide.md)**: How to document your code so it appears in Swagger.
*   ⬅️ **[Back to Index](../README.md)**
