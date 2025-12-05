import os
from cryptography.hazmat.primitives import serialization
import hvac
import hvac.exceptions

class Config:
    # 데이터베이스 설정
    DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql://postgres:postgres@localhost:5432/vulnerable_db')
    
    # Flask 설정
    SECRET_KEY = os.getenv('SECRET_KEY', 'flask-secret-key-12345')
    DEBUG = os.getenv('FLASK_ENV') == 'development'
    
    # Vault 설정
    VAULT_ADDR = os.getenv('VAULT_ADDR', 'http://localhost:8200')
    VAULT_TOKEN = os.getenv('VAULT_TOKEN', 'root-token')
    
    @staticmethod
    def get_vault_client():
        """Vault 클라이언트 생성"""
        client = hvac.Client(url=Config.VAULT_ADDR, token=Config.VAULT_TOKEN)
        return client
    
    @staticmethod
    def load_private_key_from_vault():
        """Vault KV에서 RSA 개인키 로드"""
        client = Config.get_vault_client()
        try:
            # Vault 연결 확인
            if not client.is_authenticated():
                raise Exception("Vault 인증 실패. 토큰을 확인하세요.")
            
            response = client.secrets.kv.v2.read_secret_version(path='jwt-signing-key')
            if not response or 'data' not in response or 'data' not in response['data']:
                raise Exception("Vault KV에서 키를 찾을 수 없습니다. Vault 초기화가 필요합니다.")
            
            data = response['data']['data']
            if 'private_key' not in data:
                raise Exception("Vault KV에 private_key가 없습니다. Vault 초기화 스크립트를 실행하세요.")
            
            private_key_pem = data['private_key']
            return serialization.load_pem_private_key(
                private_key_pem.encode('utf-8'),
                password=None
            )
        except hvac.exceptions.InvalidPath:
            raise Exception("Vault KV 경로 'secret/jwt-signing-key'를 찾을 수 없습니다. Vault 초기화 스크립트를 실행하세요: bash scripts/vault/init_vault.sh")
        except Exception as e:
            error_msg = str(e)
            if "404" in error_msg or "not found" in error_msg.lower():
                raise Exception("Vault KV에 키가 저장되지 않았습니다. Vault 초기화 스크립트를 실행하세요: bash scripts/vault/init_vault.sh")
            raise Exception(f"Vault에서 개인키를 로드할 수 없습니다: {error_msg}")
    
    @staticmethod
    def load_public_key_from_vault():
        """Vault KV에서 RSA 공개키 로드"""
        client = Config.get_vault_client()
        try:
            # Vault 연결 확인
            if not client.is_authenticated():
                raise Exception("Vault 인증 실패. 토큰을 확인하세요.")
            
            response = client.secrets.kv.v2.read_secret_version(path='jwt-signing-key')
            if not response or 'data' not in response or 'data' not in response['data']:
                raise Exception("Vault KV에서 키를 찾을 수 없습니다. Vault 초기화가 필요합니다.")
            
            data = response['data']['data']
            if 'public_key' not in data:
                raise Exception("Vault KV에 public_key가 없습니다. Vault 초기화 스크립트를 실행하세요.")
            
            public_key_pem = data['public_key']
            return serialization.load_pem_public_key(
                public_key_pem.encode('utf-8')
            )
        except hvac.exceptions.InvalidPath:
            raise Exception("Vault KV 경로 'secret/jwt-signing-key'를 찾을 수 없습니다. Vault 초기화 스크립트를 실행하세요: bash scripts/vault/init_vault.sh")
        except Exception as e:
            error_msg = str(e)
            if "404" in error_msg or "not found" in error_msg.lower():
                raise Exception("Vault KV에 키가 저장되지 않았습니다. Vault 초기화 스크립트를 실행하세요: bash scripts/vault/init_vault.sh")
            raise Exception(f"Vault에서 공개키를 로드할 수 없습니다: {error_msg}")

