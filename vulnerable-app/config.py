import os
from cryptography.hazmat.primitives import serialization

class Config:
    # 데이터베이스 설정
    DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql://postgres:postgres@localhost:5432/vulnerable_db')
    
    # Flask 설정
    SECRET_KEY = os.getenv('SECRET_KEY', 'flask-secret-key-12345')
    DEBUG = os.getenv('FLASK_ENV') == 'development'
    
    # RSA 키 파일 경로
    PRIVATE_KEY_PATH = os.path.join(os.path.dirname(__file__), 'private_key.pem')
    PUBLIC_KEY_PATH = os.path.join(os.path.dirname(__file__), 'public_key.pem')
    
    @staticmethod
    def load_private_key():
        """RSA 개인키 로드"""
        with open(Config.PRIVATE_KEY_PATH, 'rb') as f:
            return serialization.load_pem_private_key(
                f.read(),
                password=None
            )
    
    @staticmethod
    def load_public_key():
        """RSA 공개키 로드"""
        with open(Config.PUBLIC_KEY_PATH, 'rb') as f:
            return serialization.load_pem_public_key(
                f.read()
            )
    
    @staticmethod
    def get_private_key_pem():
        """RSA 개인키를 PEM 형식으로 반환 (문자열)"""
        with open(Config.PRIVATE_KEY_PATH, 'r') as f:
            return f.read()
    
    @staticmethod
    def get_public_key_pem():
        """RSA 공개키를 PEM 형식으로 반환 (문자열)"""
        with open(Config.PUBLIC_KEY_PATH, 'r') as f:
            return f.read()

