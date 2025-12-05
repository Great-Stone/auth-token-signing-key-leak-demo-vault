#!/bin/sh
# Vault 초기화 스크립트 (통합 버전)
# Vault가 준비될 때까지 대기하고, KV v2와 Transit 엔진을 활성화하고 키를 설정

# set -e를 제거하여 일부 명령 실패 시에도 계속 진행

VAULT_ADDR=${VAULT_ADDR:-"http://localhost:8200"}
VAULT_TOKEN=${VAULT_TOKEN:-"root-token"}
MAX_WAIT=${MAX_WAIT:-60}

echo "=========================================="
echo "Vault 초기화 스크립트 시작"
echo "=========================================="

# Vault가 준비될 때까지 대기
echo "Vault가 준비될 때까지 대기 중..."
export VAULT_ADDR
export VAULT_TOKEN
WAITED=0
while [ $WAITED -lt $MAX_WAIT ]; do
    if vault status > /dev/null 2>&1; then
        echo "✅ Vault가 준비되었습니다."
        break
    fi
    echo "  Vault 대기 중... (${WAITED}/${MAX_WAIT}초)"
    sleep 2
    WAITED=$((WAITED + 2))
done

if [ $WAITED -ge $MAX_WAIT ]; then
    echo "⚠️ Vault가 ${MAX_WAIT}초 내에 준비되지 않았습니다."
    exit 1
fi

# Vault 인증 확인 (dev 모드에서는 자동으로 인증됨)
export VAULT_ADDR
export VAULT_TOKEN
# dev 모드에서는 vault status로 확인하면 충분
if ! vault status > /dev/null 2>&1; then
    echo "⚠️ Vault에 연결할 수 없습니다."
    exit 1
fi

echo ""
echo "=========================================="
echo "KV v2 엔진 활성화"
echo "=========================================="
vault secrets enable -path=secret kv-v2 2>/dev/null && echo "✅ KV v2 엔진이 활성화되었습니다." || echo "ℹ️  KV v2 엔진이 이미 활성화되어 있습니다."

echo ""
echo "=========================================="
echo "RSA 키를 Vault KV에 저장"
echo "=========================================="

# 여러 경로에서 키 파일 찾기
PRIVATE_KEY_FILE=""
for path in "/vault/vulnerable-app/private_key.pem" "/app/../vulnerable-app/private_key.pem" "./vulnerable-app/private_key.pem" "../vulnerable-app/private_key.pem" "/vault/scripts/../../vulnerable-app/private_key.pem"; do
    if [ -f "$path" ]; then
        PRIVATE_KEY_FILE="$path"
        echo "✅ 개인키 파일 발견: $path"
        break
    fi
done

if [ -n "$PRIVATE_KEY_FILE" ]; then
    PRIVATE_KEY=$(cat "$PRIVATE_KEY_FILE")
    
    # 공개키 파일 찾기
    PUBLIC_KEY_FILE="${PRIVATE_KEY_FILE%private_key.pem}public_key.pem"
    if [ ! -f "$PUBLIC_KEY_FILE" ]; then
        # 다른 경로 시도
        for pub_path in "/vault/vulnerable-app/public_key.pem" "/app/../vulnerable-app/public_key.pem" "./vulnerable-app/public_key.pem" "../vulnerable-app/public_key.pem"; do
            if [ -f "$pub_path" ]; then
                PUBLIC_KEY_FILE="$pub_path"
                break
            fi
        done
    fi
    
    if [ -f "$PUBLIC_KEY_FILE" ]; then
        PUBLIC_KEY=$(cat "$PUBLIC_KEY_FILE")
        echo "✅ 공개키 파일 발견: $PUBLIC_KEY_FILE"
        vault kv put secret/jwt-signing-key private_key="$PRIVATE_KEY" public_key="$PUBLIC_KEY" 2>/dev/null && \
            echo "✅ 개인키와 공개키가 Vault KV에 저장되었습니다." || \
            echo "ℹ️  키가 이미 저장되어 있거나 저장에 실패했습니다."
    else
        # 공개키 파일이 없으면 개인키만 저장
        vault kv put secret/jwt-signing-key private_key="$PRIVATE_KEY" 2>/dev/null && \
            echo "✅ 개인키가 Vault KV에 저장되었습니다." || \
            echo "ℹ️  키가 이미 저장되어 있거나 저장에 실패했습니다."
        echo "⚠️  공개키 파일을 찾을 수 없습니다. 공개키는 별도로 저장해야 합니다."
    fi
else
    echo "⚠️  private_key.pem 파일을 찾을 수 없습니다."
    echo "   수동으로 키를 저장하려면 다음 명령을 사용하세요:"
    echo "   vault kv put secret/jwt-signing-key private_key=\"\$(cat vulnerable-app/private_key.pem)\" public_key=\"\$(cat vulnerable-app/public_key.pem)\""
fi

# 공개키를 별도로 저장 (아직 저장되지 않은 경우)
if [ -z "$PUBLIC_KEY_FILE" ] || [ ! -f "$PUBLIC_KEY_FILE" ]; then
    PUBLIC_KEY_FILE=""
    for path in "/vault/vulnerable-app/public_key.pem" "/app/../vulnerable-app/public_key.pem" "./vulnerable-app/public_key.pem" "../vulnerable-app/public_key.pem" "/vault/scripts/../../vulnerable-app/public_key.pem"; do
        if [ -f "$path" ]; then
            PUBLIC_KEY_FILE="$path"
            break
        fi
    done
fi

if [ -n "$PUBLIC_KEY_FILE" ] && [ -f "$PUBLIC_KEY_FILE" ]; then
    # 이미 저장되었는지 확인 (jq 없이 간단히 확인)
    EXISTING=$(vault kv get -format=json secret/jwt-signing-key 2>/dev/null | grep -o '"public_key"[[:space:]]*:[[:space:]]*"[^"]*"' || echo "")
    if [ -z "$EXISTING" ]; then
        PUBLIC_KEY=$(cat "$PUBLIC_KEY_FILE")
        vault kv patch secret/jwt-signing-key public_key="$PUBLIC_KEY" 2>/dev/null || \
            vault kv put secret/jwt-signing-key public_key="$PUBLIC_KEY" 2>/dev/null && \
            echo "✅ 공개키가 Vault KV에 저장되었습니다." || \
            echo "ℹ️  공개키 저장에 실패했습니다."
    else
        echo "ℹ️  공개키가 이미 Vault KV에 저장되어 있습니다."
    fi
fi

echo ""
echo "=========================================="
echo "Transit 엔진 활성화"
echo "=========================================="
vault secrets enable transit 2>/dev/null && echo "✅ Transit 엔진이 활성화되었습니다." || echo "ℹ️  Transit 엔진이 이미 활성화되어 있습니다."

echo ""
echo "=========================================="
echo "Transit 키 생성"
echo "=========================================="
vault write -f transit/keys/jwt-signing-key \
    type=rsa-2048 \
    exportable=false \
    2>/dev/null && echo "✅ Transit 키가 생성되었습니다." || echo "ℹ️  Transit 키가 이미 존재합니다."

echo ""
echo "=========================================="
echo "✅ Vault 초기화 완료!"
echo "=========================================="
