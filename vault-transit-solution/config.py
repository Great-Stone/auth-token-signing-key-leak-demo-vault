import os
import hvac

class Config:
    # 데이터베이스 설정
    DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql://postgres:postgres@localhost:5432/vulnerable_db')
    
    # Flask 설정
    SECRET_KEY = os.getenv('SECRET_KEY', 'flask-secret-key-12345')
    DEBUG = os.getenv('FLASK_ENV') == 'development'
    
    # Vault 설정
    VAULT_ADDR = os.getenv('VAULT_ADDR', 'http://localhost:8200')
    VAULT_TOKEN = os.getenv('VAULT_TOKEN', 'root-token')
    TRANSIT_KEY_NAME = 'jwt-signing-key'
    
    @staticmethod
    def get_vault_client():
        """Vault 클라이언트 생성"""
        client = hvac.Client(url=Config.VAULT_ADDR, token=Config.VAULT_TOKEN)
        return client

