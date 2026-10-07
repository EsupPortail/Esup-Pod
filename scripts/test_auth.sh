#!/bin/bash
# -----------------------------------------------------------------------------
# Esup-Pod - API Curl Test - Authentication App
# -----------------------------------------------------------------------------
set -e

SCRIPT_DIR=$(dirname "$0")
source "$SCRIPT_DIR/test_base.sh"

wait_for_api
setup_test_users
get_auth_token
get_std_auth_token

echo "=== Testing Authentication App ==="

# 1. Users
echo -n ">>> Testing GET /api/auth/users/me/ ... "
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" -X 'GET' "$BASE_URL/api/auth/users/me/" -H "$AUTH_HEADER")
check_success "$HTTP_CODE"

echo -n ">>> Testing GET /api/auth/users/ ... "
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" -X 'GET' "$BASE_URL/api/auth/users/" -H "$AUTH_HEADER")
check_success "$HTTP_CODE"

# 2. Owners
echo -n ">>> Testing GET /api/auth/owners/ ... "
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" -X 'GET' "$BASE_URL/api/auth/owners/" -H "$AUTH_HEADER")
check_success "$HTTP_CODE"

# 3. Sites
echo -n ">>> Testing GET /api/auth/sites/ ... "
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" -X 'GET' "$BASE_URL/api/auth/sites/" -H "$AUTH_HEADER")
check_success "$HTTP_CODE"

# 4. Access Groups
echo -n ">>> Testing GET /api/auth/access-groups/ ... "
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" -X 'GET' "$BASE_URL/api/auth/access-groups/" -H "$AUTH_HEADER")
check_success "$HTTP_CODE"

echo -n ">>> Testing POST /api/auth/access-groups/ ... "
HTTP_CODE=$(curl_post_json "/api/auth/access-groups/" "$AUTH_HEADER" '{"display_name": "Test AG", "code_name": "test_ag", "sites": [1]}')
check_success "$HTTP_CODE"
AG_ID=$(cat response.json | get_val "id")

if [ -n "$AG_ID" ]; then
    echo -n ">>> Testing PATCH /api/auth/access-groups/$AG_ID/ ... "
    HTTP_CODE=$(curl_patch "/api/auth/access-groups/$AG_ID/" "$AUTH_HEADER" '{"display_name": "Test AG Updated", "sites": [1]}')
    check_success "$HTTP_CODE"

    echo -n ">>> Testing DELETE /api/auth/access-groups/$AG_ID/ ... "
    HTTP_CODE=$(curl_delete "/api/auth/access-groups/$AG_ID/" "$AUTH_HEADER")
    check_success "$HTTP_CODE"
fi

# 5. Groups
echo -n ">>> Testing GET /api/auth/groups/ ... "
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" -X 'GET' "$BASE_URL/api/auth/groups/" -H "$AUTH_HEADER")
check_success "$HTTP_CODE"

echo -n ">>> Testing POST /api/auth/groups/ ... "
HTTP_CODE=$(curl_post_json "/api/auth/groups/" "$AUTH_HEADER" '{"name": "test-group"}')
check_success "$HTTP_CODE"
GRP_ID=$(cat response.json | get_val "id")

if [ -n "$GRP_ID" ]; then
    echo -n ">>> Testing DELETE /api/auth/groups/$GRP_ID/ (Standard User - expect 403) ... "
    HTTP_CODE=$(curl_delete "/api/auth/groups/$GRP_ID/" "$STD_AUTH_HEADER")
    check_error "$HTTP_CODE" "403"

    echo -n ">>> Testing DELETE /api/auth/groups/$GRP_ID/ ... "
    HTTP_CODE=$(curl_delete "/api/auth/groups/$GRP_ID/" "$AUTH_HEADER")
    check_success "$HTTP_CODE"
fi

echo "=== Authentication App Tests Passed ==="
