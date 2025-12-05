from flask import Flask, request, jsonify, render_template, session, redirect, url_for
from auth import hash_password, verify_password, create_token, verify_token
from database import get_user_by_username, get_user_by_id, get_user_by_username_with_hash
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
        user_with_hash = get_user_by_username_with_hash(username)
        if not user_with_hash or not verify_password(password, user_with_hash['password_hash']):
            return render_template('login.html', error='비밀번호가 올바르지 않습니다.')
        
        # JWT 토큰 생성 (Vault KV에서 키 로드)
        try:
            token = create_token(
                user_id=user['id'],
                username=user['username'],
                email=user['email']
            )
        except Exception as e:
            return render_template('login.html', error=f'토큰 생성 실패: {str(e)}')
        
        # 세션에 저장
        session['token'] = token
        session['user_id'] = user['id']
        session['username'] = user['username']
        
        # 사용자 정보 페이지로 리다이렉트
        return redirect(url_for('user_info', user_id=user['id']))
    
    return render_template('login.html')

@app.route('/user/<int:user_id>')
def user_info(user_id):
    """
    사용자 정보 페이지
    Vault KV에서 공개키를 로드하여 토큰 검증
    """
    # 토큰 가져오기 (세션 또는 헤더에서)
    token = request.headers.get('Authorization', '').replace('Bearer ', '')
    if not token:
        token = session.get('token')
    
    if not token:
        return redirect(url_for('login'))
    
    # Vault KV에서 공개키를 로드하여 토큰 검증
    decoded_token = verify_token(token)
    
    if not decoded_token:
        return redirect(url_for('login'))
    
    # 토큰의 user_id와 요청한 user_id 일치 확인
    if decoded_token.get('user_id') != user_id:
        return jsonify({'error': '토큰의 user_id와 요청한 user_id가 일치하지 않습니다.'}), 403
    
    # 사용자 정보 조회
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
    API 엔드포인트 - Vault KV에서 공개키를 로드하여 토큰 검증
    """
    token = request.headers.get('Authorization', '').replace('Bearer ', '')
    
    if not token:
        token = session.get('token')
    
    if not token:
        return jsonify({'error': '토큰이 필요합니다.'}), 401
    
    # Vault KV에서 공개키를 로드하여 토큰 검증
    decoded_token = verify_token(token)
    
    if not decoded_token:
        return jsonify({'error': '토큰 검증 실패'}), 401
    
    # 토큰의 user_id와 요청한 user_id 일치 확인
    if decoded_token.get('user_id') != user_id:
        return jsonify({'error': '토큰의 user_id와 요청한 user_id가 일치하지 않습니다.'}), 403
    
    # 사용자 정보 조회
    user = get_user_by_id(user_id)
    
    if not user:
        return jsonify({'error': '사용자를 찾을 수 없습니다.'}), 404
    
    return jsonify({
        'id': user['id'],
        'username': user['username'],
        'email': user['email'],
        'phone_num': user['phone_num'],
        'address': user['address'],
        'token_info': decoded_token,
        'vault_info': '키는 Vault KV에서 동적으로 로드되었습니다.'
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)

