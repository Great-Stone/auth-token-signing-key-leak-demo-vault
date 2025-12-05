import hashlib
import jwt
import base64
import json
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
    Vault Transit API를 통해 서명 (키는 Vault에서 관리되며 앱에서 직접 접근 불가)
    """
    now = datetime.utcnow()
    payload = {
        'user_id': user_id,
        'username': username,
        'email': email,
        'iat': int(now.timestamp()),
        'exp': int((now + timedelta(hours=24)).timestamp()),
        'iss': 'vault-transit-app'
    }
    
    # JWT 헤더와 페이로드 생성
    header = {'alg': 'RS256', 'typ': 'JWT'}
    header_b64 = base64.urlsafe_b64encode(
        jwt.encode(header, '', algorithm='none').split('.')[0].encode()
    ).decode().rstrip('=')
    
    payload_json = jwt.encode(payload, '', algorithm='none').split('.')[1]
    payload_b64 = payload_json  # 이미 base64 인코딩됨
    
    # 서명할 데이터 (JWT 표준 형식)
    signing_input = f"{header_b64}.{payload_b64}"
    
    # Vault Transit API 호출: 서명을 Vault에 위임 (키는 Vault에서 관리)
    client = Config.get_vault_client()
    try:
        # Transit은 바이너리 데이터를 서명하므로, 서명할 데이터를 base64로 인코딩
        signing_input_b64 = base64.b64encode(signing_input.encode('utf-8')).decode('utf-8')
        # Vault Transit API를 통해 서명 (키는 앱에서 직접 접근 불가)
        response = client.secrets.transit.sign_data(
            name=Config.TRANSIT_KEY_NAME,
            hash_input=signing_input_b64,
            signature_algorithm='pss'
        )
        
        # Transit 서명 형식: vault:v1:... 에서 실제 서명 부분만 추출
        signature = response['data']['signature']
        if signature.startswith('vault:v1:'):
            signature_part = signature[9:]  # 'vault:v1:' 제거
        else:
            signature_part = signature
        
        # Base64 디코딩 후 URL-safe 인코딩으로 변환
        try:
            signature_bytes = base64.b64decode(signature_part)
            signature_b64 = base64.urlsafe_b64encode(signature_bytes).decode().rstrip('=')
        except:
            # 이미 URL-safe 형식일 수 있음
            signature_b64 = signature_part.replace('+', '-').replace('/', '_').rstrip('=')
        
        token = f"{header_b64}.{payload_b64}.{signature_b64}"
        return token
    except Exception as e:
        raise Exception(f"Vault Transit 서명 실패: {str(e)}")

def verify_token(token):
    """
    JWT 토큰 검증
    Vault Transit API를 통해 서명 검증 (키는 Vault에서 관리되며 앱에서 직접 접근 불가)
    """
    try:
        parts = token.split('.')
        if len(parts) != 3:
            return None
        
        header_b64, payload_b64, signature_b64 = parts
        signing_input = f"{header_b64}.{payload_b64}"
        
        # Vault Transit API를 통해 서명 검증 (키는 Vault에서 관리되며 앱에서 직접 접근 불가)
        client = Config.get_vault_client()
        
        # 서명을 Transit 형식으로 변환
        signature_bytes = base64.urlsafe_b64decode(signature_b64 + '==')
        signature_b64_std = base64.b64encode(signature_bytes).decode()
        transit_signature = f"vault:v1:{signature_b64_std}"
        
        try:
            # 서명할 데이터를 base64로 인코딩
            signing_input_b64 = base64.b64encode(signing_input.encode('utf-8')).decode('utf-8')
            # Vault Transit API 호출: 서명 검증을 Vault에 위임
            response = client.secrets.transit.verify_signed_data(
                name=Config.TRANSIT_KEY_NAME,
                hash_input=signing_input_b64,
                signature=transit_signature,
                signature_algorithm='pss'
            )
            
            if response['data']['valid']:
                # 페이로드를 직접 base64 디코딩하여 파싱
                try:
                    # JWT 토큰에서 페이로드 부분 추출 (두 번째 부분)
                    payload_b64 = parts[1]
                    # padding 추가
                    padding = 4 - len(payload_b64) % 4
                    if padding != 4:
                        payload_b64 += '=' * padding
                    # base64 디코딩
                    payload_bytes = base64.urlsafe_b64decode(payload_b64)
                    payload = json.loads(payload_bytes.decode('utf-8'))
                    return payload
                except Exception as e:
                    print(f"페이로드 디코딩 오류: {e}")
                    return None
            else:
                return None
        except Exception as e:
            print(f"Vault Transit 검증 오류: {e}")
            return None
    except Exception as e:
        print(f"토큰 검증 오류: {e}")
        return None

