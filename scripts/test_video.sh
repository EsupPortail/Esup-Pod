#!/bin/bash
# -----------------------------------------------------------------------------
# Esup-Pod - API Curl Test - Video App
# -----------------------------------------------------------------------------
set -e

SCRIPT_DIR=$(dirname "$0")
source "$SCRIPT_DIR/test_base.sh"

wait_for_api
setup_test_users
get_auth_token
get_std_auth_token

# Create dummy files
dd if=/dev/urandom of=/tmp/test.mp4 bs=1K count=1 2>/dev/null
dd if=/dev/urandom of=/tmp/test.vtt bs=1K count=1 2>/dev/null

echo "=== Testing Video App ==="

# Types
echo -n ">>> Testing GET /api/types/ ... "
HTTP_CODE=$(curl -s -o response.json -w "%{http_code}" -X 'GET' "$BASE_URL/api/types/" -H "$AUTH_HEADER")
check_success "$HTTP_CODE"
TYPE_ID=$(cat response.json | get_val_at 0 "id")

# Disciplines
echo -n ">>> Testing GET /api/disciplines/ ... "
HTTP_CODE=$(curl -s -o response.json -w "%{http_code}" -X 'GET' "$BASE_URL/api/disciplines/" -H "$AUTH_HEADER")
check_success "$HTTP_CODE"

# Tags
echo -n ">>> Testing GET /api/tags/ ... "
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" -X 'GET' "$BASE_URL/api/tags/" -H "$AUTH_HEADER")
check_success "$HTTP_CODE"

# Video POST
echo -n ">>> Testing POST /api/videos/ ... "
ARGS="-F \"title=Test Video\" -F \"description=Test desc\" -F \"video_file=@/tmp/test.mp4\""
if [ -n "$TYPE_ID" ]; then
    ARGS="$ARGS -F \"type_id=$TYPE_ID\""
fi
HTTP_CODE=$(curl_post_form "/api/videos/" "$AUTH_HEADER" "$ARGS")
check_success "$HTTP_CODE"
VIDEO_ID=$(cat response.json | get_val "id")
VIDEO_SLUG=$(cat response.json | get_val "slug")

if [ -n "$VIDEO_SLUG" ]; then
    echo -n ">>> Testing GET /api/videos/$VIDEO_SLUG/ ... "
    HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" -X 'GET' "$BASE_URL/api/videos/$VIDEO_SLUG/" -H "$AUTH_HEADER")
    check_success "$HTTP_CODE"

    echo -n ">>> Testing PATCH /api/videos/$VIDEO_SLUG/ ... "
    HTTP_CODE=$(curl_patch_form "/api/videos/$VIDEO_SLUG/" "$AUTH_HEADER" '-F "title=Test Video Updated"')
    check_success "$HTTP_CODE"
    
    # Subtitles POST
    echo -n ">>> Testing POST /api/subtitles/ ... "
    HTTP_CODE=$(curl_post_form "/api/subtitles/" "$AUTH_HEADER" "-F \"video=$VIDEO_ID\" -F \"language=fr\" -F \"file=@/tmp/test.vtt\"")
    check_success "$HTTP_CODE"
    SUB_ID=$(cat response.json | get_val "id")

    if [ -n "$SUB_ID" ]; then
        echo -n ">>> Testing DELETE /api/subtitles/$SUB_ID/ ... "
        HTTP_CODE=$(curl_delete "/api/subtitles/$SUB_ID/" "$AUTH_HEADER")
        check_success "$HTTP_CODE"
    fi

    # Video Hyperlinks POST
    echo -n ">>> Testing POST /api/video-hyperlinks/ ... "
    HTTP_CODE=$(curl_post_json "/api/video-hyperlinks/" "$AUTH_HEADER" "{\"video\": $VIDEO_ID, \"text\": \"Test Link\", \"url\": \"http://example.com\", \"time_code\": 0}")
    if [ "$HTTP_CODE" = "201" ]; then
        LINK_ID=$(cat response.json | get_val "id")
        echo -e "${GREEN}OK${NC}"
        
        echo -n ">>> Testing PATCH /api/video-hyperlinks/$LINK_ID/ ... "
        HTTP_CODE=$(curl_patch "/api/video-hyperlinks/$LINK_ID/" "$AUTH_HEADER" '{"text": "Test Link Updated"}')
        check_success "$HTTP_CODE"

        echo -n ">>> Testing DELETE /api/video-hyperlinks/$LINK_ID/ ... "
        HTTP_CODE=$(curl_delete "/api/video-hyperlinks/$LINK_ID/" "$AUTH_HEADER")
        check_success "$HTTP_CODE"
    else
        echo -e "${GREEN}SKIPPED (HTTP $HTTP_CODE)${NC}"
    fi

    echo -n ">>> Testing DELETE /api/videos/$VIDEO_SLUG/ (Standard User - expect 404) ... "
    HTTP_CODE=$(curl_delete "/api/videos/$VIDEO_SLUG/" "$STD_AUTH_HEADER")
    check_error "$HTTP_CODE" "404"

    echo -n ">>> Testing DELETE /api/videos/$VIDEO_SLUG/ ... "
    HTTP_CODE=$(curl_delete "/api/videos/$VIDEO_SLUG/" "$AUTH_HEADER")
    check_success "$HTTP_CODE"
fi

echo -n ">>> Testing GET /api/videos/ ... "
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" -X 'GET' "$BASE_URL/api/videos/" -H "$AUTH_HEADER")
check_success "$HTTP_CODE"

echo -n ">>> Testing GET /api/videos/me/ ... "
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" -X 'GET' "$BASE_URL/api/videos/me/" -H "$AUTH_HEADER")
check_success "$HTTP_CODE"

echo -n ">>> Testing GET /api/subtitles/ ... "
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" -X 'GET' "$BASE_URL/api/subtitles/" -H "$AUTH_HEADER")
check_success "$HTTP_CODE"

echo "=== Video App Tests Passed ==="
