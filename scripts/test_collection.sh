#!/bin/bash
# -----------------------------------------------------------------------------
# Esup-Pod - API Curl Test - Collection App
# -----------------------------------------------------------------------------
set -e

SCRIPT_DIR=$(dirname "$0")
source "$SCRIPT_DIR/test_base.sh"

wait_for_api
setup_test_users
get_auth_token
get_std_auth_token

echo "=== Testing Collection App ==="

# 1. Channels
echo -n ">>> Testing GET /api/collections/channels/ ... "
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" -X 'GET' "$BASE_URL/api/collections/channels/" -H "$AUTH_HEADER")
check_success "$HTTP_CODE"

echo -n ">>> Testing POST /api/collections/channels/ ... "
HTTP_CODE=$(curl_post_json "/api/collections/channels/" "$AUTH_HEADER" '{"title": "Test Channel"}')
check_success "$HTTP_CODE"
CHANNEL_SLUG=$(cat response.json | get_val "slug")

if [ -n "$CHANNEL_SLUG" ]; then
    echo -n ">>> Testing GET /api/collections/channels/$CHANNEL_SLUG/ ... "
    HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" -X 'GET' "$BASE_URL/api/collections/channels/$CHANNEL_SLUG/" -H "$AUTH_HEADER")
    check_success "$HTTP_CODE"

    echo -n ">>> Testing PATCH /api/collections/channels/$CHANNEL_SLUG/ ... "
    HTTP_CODE=$(curl_patch "/api/collections/channels/$CHANNEL_SLUG/" "$AUTH_HEADER" '{"title": "Test Channel Updated"}')
    check_success "$HTTP_CODE"

    # Themes
    echo -n ">>> Testing GET /api/collections/themes/ ... "
    HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" -X 'GET' "$BASE_URL/api/collections/themes/" -H "$AUTH_HEADER")
    check_success "$HTTP_CODE"

    echo -n ">>> Testing POST /api/collections/themes/ ... "
    CHANNEL_ID=$(cat response.json | get_val "id") # we need channel ID, it's also in response.json of channel patch or GET. Let's do a GET to get ID
    CHANNEL_RES=$(curl -s -X 'GET' "$BASE_URL/api/collections/channels/$CHANNEL_SLUG/" -H "$AUTH_HEADER")
    CHAN_ID=$(echo "$CHANNEL_RES" | get_val "id")
    
    HTTP_CODE=$(curl_post_json "/api/collections/themes/" "$AUTH_HEADER" "{\"title\": \"Test Theme\", \"channel\": $CHAN_ID}")
    check_success "$HTTP_CODE"
    THEME_SLUG=$(cat response.json | get_val "slug")

    if [ -n "$THEME_SLUG" ]; then
        echo -n ">>> Testing PATCH /api/collections/themes/$THEME_SLUG/ ... "
        HTTP_CODE=$(curl_patch "/api/collections/themes/$THEME_SLUG/" "$AUTH_HEADER" '{"title": "Test Theme Updated"}')
        check_success "$HTTP_CODE"
        
        echo -n ">>> Testing DELETE /api/collections/themes/$THEME_SLUG/ ... "
        HTTP_CODE=$(curl_delete "/api/collections/themes/$THEME_SLUG/" "$AUTH_HEADER")
        check_success "$HTTP_CODE"
    fi

    echo -n ">>> Testing DELETE /api/collections/channels/$CHANNEL_SLUG/ (Standard User - expect 403) ... "
    HTTP_CODE=$(curl_delete "/api/collections/channels/$CHANNEL_SLUG/" "$STD_AUTH_HEADER")
    check_error "$HTTP_CODE" "403"

    echo -n ">>> Testing DELETE /api/collections/channels/$CHANNEL_SLUG/ ... "
    HTTP_CODE=$(curl_delete "/api/collections/channels/$CHANNEL_SLUG/" "$AUTH_HEADER")
    check_success "$HTTP_CODE"
fi

# 3. Playlists
echo -n ">>> Testing GET /api/collections/playlists/ ... "
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" -X 'GET' "$BASE_URL/api/collections/playlists/" -H "$AUTH_HEADER")
check_success "$HTTP_CODE"

echo -n ">>> Testing POST /api/collections/playlists/ ... "
HTTP_CODE=$(curl_post_json "/api/collections/playlists/" "$AUTH_HEADER" '{"title": "Test Playlist"}')
check_success "$HTTP_CODE"
PLAYLIST_SLUG=$(cat response.json | get_val "slug")

if [ -n "$PLAYLIST_SLUG" ]; then
    echo -n ">>> Testing PATCH /api/collections/playlists/$PLAYLIST_SLUG/ ... "
    HTTP_CODE=$(curl_patch "/api/collections/playlists/$PLAYLIST_SLUG/" "$AUTH_HEADER" '{"title": "Test Playlist Updated"}')
    check_success "$HTTP_CODE"

    echo -n ">>> Testing DELETE /api/collections/playlists/$PLAYLIST_SLUG/ ... "
    HTTP_CODE=$(curl_delete "/api/collections/playlists/$PLAYLIST_SLUG/" "$AUTH_HEADER")
    check_success "$HTTP_CODE"
fi

# 4. Favorites
echo -n ">>> Testing GET /api/collections/favorites/ ... "
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" -X 'GET' "$BASE_URL/api/collections/favorites/" -H "$AUTH_HEADER")
check_success "$HTTP_CODE"
# To test favorites POST, we need a video. We assume testing GET is sufficient for now since Video tests handle video creation, unless we create one here.
# For simplicity, we just test GET favorites

echo "=== Collection App Tests Passed ==="
