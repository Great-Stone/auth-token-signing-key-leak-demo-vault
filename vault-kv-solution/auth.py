import hashlib
import jwt
from datetime import datetime, timedelta
from config import Config

def hash_password(password):
    """비밀번호를 SHA256으로 해시"""
    return hashlib.sha256(password.encode('utf-8')).hexdigest()

def verify_password(password, password_hash):
    """비밀번호 검증"""
    return hash_password(password) == password_hash

def create_token(user_id, username, email):
    """
    JWT 토큰 생성 (RS256)
    Vault KV에서 개인키를 동적으로 로드하여 사용
    """
    now = datetime.utcnow()
    payload = {
        'user_id': user_id,
        'username': username,
        'email': email,
        'iat': int(now.timestamp()),
        'exp': int((now + timedelta(hours=24)).timestamp()),
        'iss': 'vault-kv-app'
    }
    
    # Vault KV에서 개인키 로드
    private_key = Config.load_private_key_from_vault()
    token = jwt.encode(payload, private_key, algorithm='RS256')
    return token

def verify_token(token):
    """
    JWT 토큰 검증
    Vault KV에서 공개키를 동적으로 로드하여 검증
    """
    try:
        # Vault KV에서 공개키 로드하여 검증
        public_key = Config.load_public_key_from_vault()
        decoded = jwt.decode(token, public_key, algorithms=['RS256'])
        return decoded
    except jwt.ExpiredSignatureError:
        # 만료된 토큰
        return None
    except jwt.InvalidTokenError as e:
        # 검증 실패
        return None
    except Exception as e:
        # Vault 접근 오류 등
        print(f"토큰 검증 오류: {e}")
        return None

