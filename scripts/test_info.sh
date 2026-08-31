#!/bin/bash
# -----------------------------------------------------------------------------
# Esup-Pod - API Curl Test - Info App
# -----------------------------------------------------------------------------
set -e

SCRIPT_DIR=$(dirname "$0")
source "$SCRIPT_DIR/test_base.sh"

wait_for_api

echo "=== Testing Info App ==="

echo -n ">>> Testing GET /api/info/conf ... "
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" -X 'GET' "$BASE_URL/api/info/conf")
check_success "$HTTP_CODE"

echo -n ">>> Testing GET /api/info/ ... "
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" -X 'GET' "$BASE_URL/api/info/")
check_success "$HTTP_CODE"

echo "=== Info App Tests Passed ==="
