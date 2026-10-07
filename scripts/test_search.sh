#!/bin/bash
# -----------------------------------------------------------------------------
# Esup-Pod - API Curl Test - Search App
# -----------------------------------------------------------------------------
set -e

SCRIPT_DIR=$(dirname "$0")
source "$SCRIPT_DIR/test_base.sh"

wait_for_api
get_auth_token

echo "=== Testing Search App ==="

# 1. Simple search
echo -n ">>> Testing GET /api/search/?q=python ... "
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" -X 'GET' "$BASE_URL/api/search/?q=python" -H "$AUTH_HEADER")
check_success "$HTTP_CODE"

# 2. Wildcard search
echo -n ">>> Testing GET /api/search/ (wildcard) ... "
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" -X 'GET' "$BASE_URL/api/search/" -H "$AUTH_HEADER")
check_success "$HTTP_CODE"

# 3. Search filters
echo -n ">>> Testing GET /api/search/?q=cours&type=cours&lang=fr ... "
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" -X 'GET' "$BASE_URL/api/search/?q=cours&type=cours&lang=fr" -H "$AUTH_HEADER")
check_success "$HTTP_CODE"

# 4. Pagination
echo -n ">>> Testing GET /api/search/?limit=5&offset=5 ... "
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" -X 'GET' "$BASE_URL/api/search/?limit=5&offset=5" -H "$AUTH_HEADER")
check_success "$HTTP_CODE"

# 5. Metadata Cache
echo -n ">>> Testing GET /api/videos/metadata/ (Search Cache) ... "
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" -X 'GET' "$BASE_URL/api/videos/metadata/")
check_success "$HTTP_CODE"

echo "=== Search App Tests Passed ==="
