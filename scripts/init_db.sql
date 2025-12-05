-- 사용자 테이블 생성
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(100) UNIQUE NOT NULL,
    password_hash VARCHAR(64) NOT NULL,  -- SHA256 해시 (64자)
    email VARCHAR(255) NOT NULL,
    phone_num VARCHAR(20),
    address TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 목업 데이터 삽입
-- 비밀번호는 모두 "password123"의 SHA256 해시
-- SHA256("password123") = ef92b778bafe771e89245b89ecbc08a44a4e166c06659911881f383d4473e94f
INSERT INTO users (username, password_hash, email, phone_num, address) VALUES
('alice', 'ef92b778bafe771e89245b89ecbc08a44a4e166c06659911881f383d4473e94f', 'alice@example.com', '010-1234-5678', '서울시 강남구 테헤란로 123'),
('bob', 'ef92b778bafe771e89245b89ecbc08a44a4e166c06659911881f383d4473e94f', 'bob@example.com', '010-2345-6789', '서울시 서초구 서초대로 456'),
('charlie', 'ef92b778bafe771e89245b89ecbc08a44a4e166c06659911881f383d4473e94f', 'charlie@example.com', '010-3456-7890', '서울시 송파구 올림픽로 789'),
('david', 'ef92b778bafe771e89245b89ecbc08a44a4e166c06659911881f383d4473e94f', 'david@example.com', '010-4567-8901', '서울시 마포구 홍대로 321'),
('eve', 'ef92b778bafe771e89245b89ecbc08a44a4e166c06659911881f383d4473e94f', 'eve@example.com', '010-5678-9012', '서울시 종로구 세종대로 654'),
('frank', 'ef92b778bafe771e89245b89ecbc08a44a4e166c06659911881f383d4473e94f', 'frank@example.com', '010-6789-0123', '서울시 영등포구 여의대로 987'),
('grace', 'ef92b778bafe771e89245b89ecbc08a44a4e166c06659911881f383d4473e94f', 'grace@example.com', '010-7890-1234', '서울시 강동구 천호대로 147'),
('henry', 'ef92b778bafe771e89245b89ecbc08a44a4e166c06659911881f383d4473e94f', 'henry@example.com', '010-8901-2345', '서울시 노원구 상계로 258'),
('ivy', 'ef92b778bafe771e89245b89ecbc08a44a4e166c06659911881f383d4473e94f', 'ivy@example.com', '010-9012-3456', '서울시 도봉구 도봉로 369'),
('jack', 'ef92b778bafe771e89245b89ecbc08a44a4e166c06659911881f383d4473e94f', 'jack@example.com', '010-0123-4567', '서울시 은평구 은평로 741');

