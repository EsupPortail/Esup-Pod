#!/bin/bash
# -----------------------------------------------------------------------------
# Esup-Pod - API Curl Test - Encoding App
# -----------------------------------------------------------------------------
set -e

SCRIPT_DIR=$(dirname "$0")
source "$SCRIPT_DIR/test_base.sh"

wait_for_api
get_auth_token

echo "=== Testing Encoding App ==="

# 1. Webhook
echo -n ">>> Testing POST /api/encoding/webhook/ (Expect 401) ... "
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" -X 'POST' "$BASE_URL/api/encoding/webhook/" -H "$AUTH_HEADER")
if [ "$HTTP_CODE" != "401" ]; then
    echo -e "${RED}FAILED (HTTP $HTTP_CODE)${NC}"
    exit 1
else
    echo -e "${GREEN}OK${NC}"
fi

echo "=== Encoding App Tests Passed ==="
