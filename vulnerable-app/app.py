from flask import Flask, request, jsonify, render_template, session, redirect, url_for
from auth import hash_password, verify_password, create_token, verify_token
from database import get_user_by_username, get_user_by_id
from config import Config
import jwt

app = Flask(__name__)
app.secret_key = Config.SECRET_KEY

@app.route('/')
def index():
    """메인 페이지"""
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    """로그인 페이지 및 처리"""
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        if not username or not password:
            return render_template('login.html', error='사용자명과 비밀번호를 입력하세요.')
        
        # 데이터베이스에서 사용자 조회
        user = get_user_by_username(username)
        
        if not user:
            return render_template('login.html', error='사용자를 찾을 수 없습니다.')
        
        # 비밀번호 검증
        # 실제로는 데이터베이스에서 password_hash를 가져와야 하지만,
        # 여기서는 간단히 사용자 정보만 반환하는 것으로 가정
        # 실제 검증은 데이터베이스 쿼리를 수정해야 함
        user_with_hash = get_user_by_username_with_hash(username)
        if not user_with_hash or not verify_password(password, user_with_hash['password_hash']):
            return render_template('login.html', error='비밀번호가 올바르지 않습니다.')
        
        # JWT 토큰 생성 (내부적으로만 사용되는 API)
        token = create_token(
            user_id=user['id'],
            username=user['username'],
            email=user['email']
        )
        
        # 세션에 저장
        session['token'] = token
        session['user_id'] = user['id']
        session['username'] = user['username']
        
        # 사용자 정보 페이지로 리다이렉트
        return redirect(url_for('user_info', user_id=user['id']))
    
    return render_template('login.html')

def get_user_by_username_with_hash(username):
    """비밀번호 해시 포함 사용자 조회"""
    from database import get_db_connection
    from psycopg2.extras import RealDictCursor
    
    conn = get_db_connection()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                "SELECT id, username, password_hash, email, phone_num, address FROM users WHERE username = %s",
                (username,)
            )
            return cur.fetchone()
    finally:
        conn.close()

@app.route('/user/<int:user_id>')
def user_info(user_id):
    """
    사용자 정보 페이지
    취약점: 해커가 임의로 토큰을 사용하여 페이지를 호출할 수 있음
    """
    # 토큰 가져오기 (세션 또는 헤더에서)
    token = request.headers.get('Authorization', '').replace('Bearer ', '')
    if not token:
        token = session.get('token')
    
    if not token:
        return redirect(url_for('login'))
    
    # 토큰 검증 (서명 검증은 정상적으로 작동)
    decoded_token = verify_token(token)
    
    if not decoded_token:
        # 부가 취약점: 검증 실패 시에도 서명 검증 없이 디코딩 시도
        try:
            decoded_token = jwt.decode(token, options={"verify_signature": False})
        except:
            return redirect(url_for('login'))
    
    # 핵심 취약점: 토큰의 user_id와 URL의 user_id를 비교하지 않음
    # 유출된 키로 서명한 토큰은 정상 검증을 통과하지만,
    # 토큰의 user_id와 요청한 user_id가 일치하는지 확인하지 않아
    # 다른 사용자 정보에 접근 가능
    user = get_user_by_id(user_id)
    
    if not user:
        return jsonify({'error': '사용자를 찾을 수 없습니다.'}), 404
    
    return render_template('user_info.html', 
                         user=user, 
                         token_info=decoded_token,
                         current_token=token)

@app.route('/api/user/<int:user_id>', methods=['GET'])
def api_user_info(user_id):
    """
    API 엔드포인트 - 토큰으로 사용자 정보 반환
    취약점: 서명 검증이 약하거나 없음
    """
    token = request.headers.get('Authorization', '').replace('Bearer ', '')
    
    # 세션에서도 토큰 가져오기 (공격 데모를 위해)
    if not token:
        token = session.get('token')
    
    if not token:
        return jsonify({'error': '토큰이 필요합니다.'}), 401
    
    # 토큰 검증 (서명 검증은 정상적으로 작동)
    decoded_token = verify_token(token)
    
    if not decoded_token:
        # 부가 취약점: 검증 실패 시에도 서명 검증 없이 디코딩 시도
        try:
            decoded_token = jwt.decode(token, options={"verify_signature": False})
        except:
            return jsonify({'error': '토큰 디코딩 실패'}), 401
    
    # 핵심 취약점: 토큰의 user_id와 URL의 user_id를 비교하지 않음
    # 유출된 키로 서명한 토큰은 정상 검증을 통과하지만,
    # 토큰의 user_id와 요청한 user_id가 일치하는지 확인하지 않아
    # 다른 사용자 정보에 접근 가능
    user = get_user_by_id(user_id)
    
    if not user:
        return jsonify({'error': '사용자를 찾을 수 없습니다.'}), 404
    
    return jsonify({
        'id': user['id'],
        'username': user['username'],
        'email': user['email'],
        'phone_num': user['phone_num'],
        'address': user['address'],
        'token_info': decoded_token
    })

@app.route('/users', methods=['GET'])
def list_users():
    """모든 사용자 목록 (공격자가 타겟 선택용)"""
    from database import get_db_connection
    from psycopg2.extras import RealDictCursor
    
    conn = get_db_connection()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                "SELECT id, username, email FROM users ORDER BY id"
            )
            users = cur.fetchall()
            return jsonify([{
                'id': u['id'],
                'username': u['username'],
                'email': u['email']
            } for u in users])
    finally:
        conn.close()

@app.route('/attack-demo')
def attack_demo():
    """공격 데모 페이지"""
    return render_template('attack_demo.html')

@app.route('/api/generate-fake-token', methods=['POST'])
def generate_fake_token():
    """
    유출된 키로 비인증 토큰 생성 API (공격 데모용)
    실제 환경에서는 이런 API가 존재하면 안 됨
    """
    data = request.json
    user_id = data.get('user_id')
    
    if not user_id:
        return jsonify({'error': 'user_id가 필요합니다.'}), 400
    
    try:
        # 타겟 사용자 정보 조회
        user = get_user_by_id(user_id)
        if not user:
            return jsonify({'error': '사용자를 찾을 수 없습니다.'}), 404
        
        # 유출된 키로 토큰 생성 (데모용으로 같은 키 사용)
        from datetime import datetime, timedelta
        now = datetime.utcnow()
        payload = {
            'user_id': user_id,
            'username': user['username'],
            'email': user['email'],
            'iat': int(now.timestamp()),
            'exp': int((now + timedelta(hours=24)).timestamp()),
            'iss': 'vulnerable-app'
        }
        
        # 유출된 키로 서명 (데모용으로 같은 키 사용)
        private_key = Config.load_private_key()
        token = jwt.encode(payload, private_key, algorithm='RS256')
        
        return jsonify({
            'token': token,
            'payload': payload,
            'user': {
                'id': user['id'],
                'username': user['username'],
                'email': user['email']
            }
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/test-token', methods=['POST'])
def test_token():
    """
    토큰으로 사용자 정보 조회 테스트 API (공격 데모용)
    """
    data = request.json
    token = data.get('token')
    user_id = data.get('user_id')
    
    if not token:
        return jsonify({'error': '토큰이 필요합니다.'}), 400
    
    if not user_id:
        return jsonify({'error': 'user_id가 필요합니다.'}), 400
    
    try:
        # 토큰 검증
        decoded_token = verify_token(token)
        
        if not decoded_token:
            try:
                decoded_token = jwt.decode(token, options={"verify_signature": False})
            except:
                return jsonify({'error': '토큰 디코딩 실패'}), 401
        
        # 사용자 정보 조회
        user = get_user_by_id(user_id)
        
        if not user:
            return jsonify({'error': '사용자를 찾을 수 없습니다.'}), 404
        
        return jsonify({
            'success': True,
            'user': {
                'id': user['id'],
                'username': user['username'],
                'email': user['email'],
                'phone_num': user['phone_num'],
                'address': user['address']
            },
            'token_info': decoded_token,
            'message': '공격 성공! 유출된 키로 생성한 토큰으로 다른 사용자 정보에 접근했습니다.'
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/resign-token', methods=['POST'])
def resign_token():
    """
    토큰 재서명 API (공격 데모용)
    실제 환경에서는 이런 API가 존재하면 안 됨
    """
    data = request.json
    payload = data.get('payload')
    key_path = data.get('key_path')
    
    if not payload:
        return jsonify({'error': 'payload가 필요합니다.'}), 400
    
    try:
        # 유출된 키로 재서명
        if key_path:
            # 파일 경로로 키 로드
            from cryptography.hazmat.primitives import serialization
            import os
            leaked_key_path = os.path.join(os.path.dirname(__file__), '..', key_path)
            with open(leaked_key_path, 'rb') as f:
                private_key = serialization.load_pem_private_key(
                    f.read(),
                    password=None
                )
        else:
            # 기본 키 사용
            private_key = Config.load_private_key()
        
        token = jwt.encode(payload, private_key, algorithm='RS256')
        return jsonify({'token': token})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)

