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
    내부적으로만 사용되는 API
    """
    now = datetime.utcnow()
    payload = {
        'user_id': user_id,
        'username': username,
        'email': email,
        'iat': int(now.timestamp()),
        'exp': int((now + timedelta(hours=24)).timestamp()),
        'iss': 'vulnerable-app'
    }
    
    # RSA 개인키로 서명
    private_key = Config.load_private_key()
    token = jwt.encode(payload, private_key, algorithm='RS256')
    return token

def verify_token(token):
    """
    JWT 토큰 검증
    서명 검증은 정상적으로 작동합니다 (RSA 공개키로 검증).
    
    핵심 문제: 유출된 개인키로 서명한 토큰도 정상적으로 검증을 통과합니다.
    부가 취약점: 검증 실패 시에도 서명 검증 없이 디코딩을 시도합니다.
    """
    try:
        # RSA 공개키로 정상 검증
        public_key = Config.load_public_key()
        decoded = jwt.decode(token, public_key, algorithms=['RS256'])
        return decoded
    except jwt.ExpiredSignatureError:
        # 만료된 토큰
        return None
    except jwt.InvalidTokenError:
        # 부가 취약점: 검증 실패 시에도 서명 검증 없이 디코딩 시도
        try:
            decoded = jwt.decode(token, options={"verify_signature": False})
            return decoded
        except:
            return None

