#!/bin/bash
# -----------------------------------------------------------------------------
# Esup-Pod - API Curl Test - Completion App
# -----------------------------------------------------------------------------
set -e

SCRIPT_DIR=$(dirname "$0")
source "$SCRIPT_DIR/test_base.sh"

wait_for_api
get_auth_token

echo "=== Testing Completion App ==="

# 1. Contributors
echo -n ">>> Testing GET /api/contributors/ ... "
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" -X 'GET' "$BASE_URL/api/contributors/" -H "$AUTH_HEADER")
check_success "$HTTP_CODE"

echo -n ">>> Testing POST /api/contributors/ ... "
HTTP_CODE=$(curl_post_json "/api/contributors/" "$AUTH_HEADER" '{"first_name": "Test", "last_name": "Contrib"}')
check_success "$HTTP_CODE"
CONTRIB_ID=$(cat response.json | get_val "id")

if [ -n "$CONTRIB_ID" ]; then
    echo -n ">>> Testing PATCH /api/contributors/$CONTRIB_ID/ ... "
    HTTP_CODE=$(curl_patch "/api/contributors/$CONTRIB_ID/" "$AUTH_HEADER" '{"first_name": "Test Updated"}')
    check_success "$HTTP_CODE"

    echo -n ">>> Testing DELETE /api/contributors/$CONTRIB_ID/ ... "
    HTTP_CODE=$(curl_delete "/api/contributors/$CONTRIB_ID/" "$AUTH_HEADER")
    check_success "$HTTP_CODE"
fi

# 2. Contributions
echo -n ">>> Testing GET /api/contributions/ ... "
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" -X 'GET' "$BASE_URL/api/contributions/" -H "$AUTH_HEADER")
check_success "$HTTP_CODE"

# 3. Documents
echo -n ">>> Testing GET /api/documents/ ... "
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" -X 'GET' "$BASE_URL/api/documents/" -H "$AUTH_HEADER")
check_success "$HTTP_CODE"

# 4. Overlays
echo -n ">>> Testing GET /api/overlays/ ... "
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" -X 'GET' "$BASE_URL/api/overlays/" -H "$AUTH_HEADER")
check_success "$HTTP_CODE"

echo "=== Completion App Tests Passed ==="
