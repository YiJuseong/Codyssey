-- ============================================================
-- 과제 제출물 #1: 스키마 생성 스크립트 (01_schema.sql)
-- DBMS: PostgreSQL 16+
-- 도메인: 도서 대여 데이터베이스
-- ============================================================

-- [기존 테이블 초기화]
-- 반복 실행 및 재테스트 시 에러 방지를 위해 기존 테이블을 역순으로 삭제합니다.
-- CASCADE 옵션은 FK로 엮인 연관 제약조건을 함께 해제합니다.
DROP TABLE IF EXISTS rental CASCADE;
DROP TABLE IF EXISTS book CASCADE;
DROP TABLE IF EXISTS member CASCADE;
DROP TABLE IF EXISTS category CASCADE;


-- 1. 카테고리 테이블 (category)
-- - 도서의 장르/분류 정보를 관리하는 부모 테이블
CREATE TABLE category (
    category_id INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY, -- 자동 증가 PK (표준 SQL)
    category_name VARCHAR(50) NOT NULL UNIQUE                 -- [제약조건] NOT NULL + UNIQUE
);


-- 2. 회원 테이블 (member)
-- - 도서 대여 서비스를 이용하는 회원 정보를 관리하는 부모 테이블
CREATE TABLE member (
    member_id INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    email VARCHAR(100) NOT NULL UNIQUE,                       -- [제약조건] UNIQUE (중복 이메일 방지)
    name VARCHAR(50) NOT NULL,                                -- [제약조건] NOT NULL
    phone VARCHAR(20),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);


-- 3. 도서 테이블 (book)
-- - 카테고리(category) 테이블과 1:N 관계를 가지는 자식 테이블
CREATE TABLE book (
    book_id INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    title VARCHAR(150) NOT NULL,                              -- [제약조건] NOT NULL
    author VARCHAR(100) NOT NULL,
    price INT NOT NULL,
    category_id INT NOT NULL,                                 -- FK 컬럼
    CONSTRAINT fk_book_category FOREIGN KEY (category_id) REFERENCES category(category_id)
);


-- 4. 대여 기록 테이블 (rental)
-- - 회원(member) 및 도서(book) 테이블과 1:N 관계를 가지는 자식 테이블
CREATE TABLE rental (
    rental_id INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    member_id INT NOT NULL,                                   -- FK 1 컬럼
    book_id INT NOT NULL,                                     -- FK 2 컬럼
    rental_date DATE NOT NULL,                                -- 대여일
    return_date DATE,                                         -- 반납일 (대여 중이면 NULL)
    CONSTRAINT fk_rental_member FOREIGN KEY (member_id) REFERENCES member(member_id),
    CONSTRAINT fk_rental_book FOREIGN KEY (book_id) REFERENCES book(book_id)
);