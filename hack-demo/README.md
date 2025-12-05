# 해킹 데모

이 디렉토리에는 취약한 인증 시스템을 공격하는 데모 스크립트가 포함되어 있습니다.

## 파일 설명

- `exploit.py`: Python으로 작성된 공격 스크립트
- `exploit.html`: 브라우저에서 실행 가능한 공격 데모
- `generate_token.sh`: OpenSSL을 사용하여 토큰을 생성하는 쉘 스크립트
- `leaked_private_key.pem`: 유출된 RSA 개인키 (해커가 이미 획득했다고 가정)

## 실행 방법

### Python 스크립트 + UI 연동 (권장)

1. 필요한 패키지 설치:
```bash
pip3 install -r requirements.txt
```

2. 스크립트 실행:
```bash
python3 exploit.py
```

3. 생성된 토큰을 UI에 붙여넣기:
   - 스크립트가 각 단계마다 생성한 토큰을 출력합니다
   - 토큰을 복사하여 http://localhost:5001/attack-demo 의 "4단계: 직접 토큰 입력하여 테스트"에 붙여넣습니다
   - 토큰을 붙여넣으면 자동으로 토큰의 user_id가 추출되어 설정됩니다
   - 다른 사용자 ID로 접근하려면 user_id를 변경할 수 있습니다
   - "토큰 테스트" 버튼을 클릭하여 공격을 시뮬레이션합니다

### Python 스크립트만 실행

스크립트는 다음 단계를 자동으로 수행합니다:

1. 정상적으로 로그인
2. 토큰 정보 추출
3. 토큰 수정 및 재서명 (여러 사용자에 대해)
4. 타인 정보 접근

### OpenSSL을 사용한 토큰 생성 (exploit.py 없이)

Python이 없어도 OpenSSL만으로 토큰을 생성할 수 있습니다:

```bash
./generate_token.sh <user_id> <username> <email>
```

예시:
```bash
# 사용자 ID 2 (bob)의 토큰 생성
./generate_token.sh 2 bob bob@example.com

# 사용자 ID 5 (eve)의 토큰 생성  
./generate_token.sh 5 eve eve@example.com
```

생성된 토큰을 http://localhost:5001/attack-demo 의 "4단계: 직접 토큰 입력하여 테스트"에 붙여넣어 테스트할 수 있습니다.

### 브라우저 데모

1. 브라우저에서 `exploit.html` 파일을 엽니다
2. 먼저 http://localhost:5001 에서 로그인합니다
3. 각 단계별 버튼을 클릭하여 공격을 시뮬레이션합니다

## 공격 시나리오

해커는 이미 RSA 개인키를 획득했다고 가정합니다. 이 키를 사용하여:

1. 정상 로그인으로 받은 토큰의 구조를 확인
2. 토큰의 payload를 수정 (다른 사용자의 user_id로 변경)
3. 유출된 개인키로 재서명
4. 재서명한 토큰으로 다른 사용자 정보 접근

