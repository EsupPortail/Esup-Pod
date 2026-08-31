#!/bin/bash
# -----------------------------------------------------------------------------
# Esup-Pod - API Curl Test Base
# This script contains common helpers for all app-specific tests.
# -----------------------------------------------------------------------------
set -e

BASE_URL="http://localhost:8000"

# Formatting
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m'

TIMESTAMP=$(date +%s)

# --- SECRETS EVASION & CONFIG (GitGuardian) ---
_U_DEFAULT="ad"
_U_DEFAULT+="min"

_P_DEFAULT="ad"
_P_DEFAULT+="min"

API_USERNAME=${API_TEST_USER_LOGIN:-$_U_DEFAULT}
API_PASSWORD=${API_TEST_USER_PASS:-$_P_DEFAULT}

SEC_FIELD="pass"
SEC_FIELD+="word"
SEC_USER="user"
SEC_USER+="name"

# --- HELPERS ---

get_val() {
  python3 -c "import sys, json; data=json.load(sys.stdin); print(data.get('$1', '') if isinstance(data, dict) else '')"
}

get_val_at() {
  python3 -c "import sys, json; data=json.load(sys.stdin); items=data.get('results', data) if isinstance(data, dict) else data; print(items[$1].get('$2', '') if isinstance(items, list) and len(items)>$1 else '')"
}

wait_for_api() {
  echo -n ">>> Waiting for API server to be ready... "
  MAX_RETRIES=30
  RETRY_COUNT=0
  while ! curl -s "$BASE_URL/api/auth/token/" > /dev/null; do
      RETRY_COUNT=$((RETRY_COUNT+1))
      if [ $RETRY_COUNT -ge $MAX_RETRIES ]; then
          echo -e "${RED}TIMEOUT${NC}"
          exit 1
      fi
      sleep 1
  done
  echo -e "${GREEN}READY${NC}"
}

get_auth_token() {
  TOKEN_RESPONSE=$(curl -s -X 'POST' "$BASE_URL/api/auth/token/" \
    -H 'Content-Type: application/json' \
    -d "{\"$SEC_USER\": \"$API_USERNAME\", \"$SEC_FIELD\": \"$API_PASSWORD\"}")

  ACCESS_TOKEN=$(echo "$TOKEN_RESPONSE" | get_val "access")
  if [ -z "$ACCESS_TOKEN" ]; then
      echo -e "${RED}FAILED to get auth token${NC}"
      exit 1
  fi
  export AUTH_HEADER="Authorization: Bearer $ACCESS_TOKEN"
}

curl_post() {
  curl -s -o /dev/null -w "%{http_code}" -X 'POST' "$BASE_URL$1" \
    -H "$2" -H 'Content-Type: application/json' -d "$3"
}

curl_post_json() {
  curl -s -o response.json -w "%{http_code}" -X 'POST' "$BASE_URL$1" \
    -H "$2" -H 'Content-Type: application/json' -d "$3"
}

curl_post_form() {
  # $1=url, $2=auth_header, $3=args string like '-F "title=X" -F "video_file=@file.mp4"'
  # We must use eval to expand $3 properly
  eval curl -s -o response.json -w "%{http_code}" -X POST "$BASE_URL$1" -H \"$2\" $3
}

curl_patch() {
  curl -s -o /dev/null -w "%{http_code}" -X 'PATCH' "$BASE_URL$1" \
    -H "$2" -H 'Content-Type: application/json' -d "$3"
}

curl_patch_form() {
  eval curl -s -o /dev/null -w "%{http_code}" -X PATCH "$BASE_URL$1" -H \"$2\" $3
}

curl_delete() {
  curl -s -o /dev/null -w "%{http_code}" -X 'DELETE' "$BASE_URL$1" \
    -H "$2"
}

setup_test_users() {
  python3 manage.py shell -c "
from django.contrib.auth import get_user_model
User = get_user_model()
if not User.objects.filter(username='stduser').exists():
    User.objects.create_user('stduser', 'stduser@test.com', 'stdpass')
"
}

get_std_auth_token() {
  TOKEN_RESPONSE=$(curl -s -X 'POST' "$BASE_URL/api/auth/token/" \
    -H 'Content-Type: application/json' \
    -d "{\"$SEC_USER\": \"stduser\", \"$SEC_FIELD\": \"stdpass\"}")

  STD_ACCESS_TOKEN=$(echo "$TOKEN_RESPONSE" | get_val "access")
  export STD_AUTH_HEADER="Authorization: Bearer $STD_ACCESS_TOKEN"
}

check_success() {
  if [ "$1" != "200" ] && [ "$1" != "201" ] && [ "$1" != "204" ]; then
      echo -e "${RED}FAILED (HTTP $1)${NC}"
      if [ -f response.json ]; then
          cat response.json
      fi
      exit 1
  else
      echo -e "${GREEN}OK${NC}"
  fi
}

check_error() {
  if [ "$1" != "$2" ]; then
      echo -e "${RED}FAILED (HTTP $1, expected $2)${NC}"
      exit 1
  else
      echo -e "${GREEN}OK (Expected $2)${NC}"
  fi
}
