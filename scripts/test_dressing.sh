#!/bin/bash
# -----------------------------------------------------------------------------
# Esup-Pod - API Curl Test - Dressing App
# -----------------------------------------------------------------------------
set -e

SCRIPT_DIR=$(dirname "$0")
source "$SCRIPT_DIR/test_base.sh"

wait_for_api
setup_test_users
get_auth_token
get_std_auth_token

echo "=== Testing Dressing App ==="

echo -n ">>> Testing GET /api/dressing/dressing/ ... "
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" -X 'GET' "$BASE_URL/api/dressing/dressing/" -H "$AUTH_HEADER")
check_success "$HTTP_CODE"

echo -n ">>> Testing GET /api/dressing/watermarks/ ... "
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" -X 'GET' "$BASE_URL/api/dressing/watermarks/" -H "$AUTH_HEADER")
check_success "$HTTP_CODE"

echo "=== Dressing App Tests Passed ==="
