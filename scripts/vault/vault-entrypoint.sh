#!/bin/sh
# Vault 서버 시작 및 자동 초기화 엔트리포인트

# set -e를 제거하여 초기화 실패 시에도 서버가 계속 실행되도록 함

echo "=========================================="
echo "Vault 서버 시작"
echo "=========================================="

# Vault 서버를 백그라운드로 시작
vault server -dev \
    -dev-root-token-id="${VAULT_DEV_ROOT_TOKEN_ID:-root-token}" \
    -dev-listen-address="${VAULT_DEV_LISTEN_ADDRESS:-0.0.0.0:8200}" &

VAULT_PID=$!

# Vault가 준비될 때까지 대기
echo "Vault 서버가 준비될 때까지 대기 중..."
export VAULT_ADDR="http://localhost:8200"
MAX_WAIT=30
WAITED=0
while [ $WAITED -lt $MAX_WAIT ]; do
    if vault status > /dev/null 2>&1; then
        echo "✅ Vault 서버가 준비되었습니다."
        break
    fi
    sleep 1
    WAITED=$((WAITED + 1))
done

if [ $WAITED -ge $MAX_WAIT ]; then
    echo "⚠️ Vault 서버가 준비되지 않았습니다. 계속 진행합니다..."
fi

# Vault 초기화 스크립트 실행
echo ""
echo "=========================================="
echo "Vault 초기화 시작"
echo "=========================================="

export VAULT_ADDR="http://localhost:8200"
export VAULT_TOKEN="${VAULT_DEV_ROOT_TOKEN_ID:-root-token}"

# 초기화 스크립트 실행
if [ -f "/vault/scripts/init_vault.sh" ]; then
    sh /vault/scripts/init_vault.sh
elif [ -f "/app/../scripts/vault/init_vault.sh" ]; then
    sh /app/../scripts/vault/init_vault.sh
else
    echo "⚠️ 초기화 스크립트를 찾을 수 없습니다."
fi

# Vault 서버를 포그라운드로 유지
echo ""
echo "=========================================="
echo "Vault 서버 실행 중..."
echo "=========================================="
wait $VAULT_PID

