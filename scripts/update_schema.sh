#!/bin/bash
set -e

echo "Generating OpenAPI schema..."
python manage.py spectacular --file docs/api-docs.yaml
echo "Schema updated at docs/api-docs.yaml"
