-- ============================================================
-- 과제 제출물 #1: 스키마 생성 스크립트 (01_schema.sql)
-- DBMS: PostgreSQL 16+
-- 도메인: 도서 대여 데이터베이스

-- [정규화 설계 근거]
-- 1. 1NF (제1정규형): 모든 컬럼은 원자값(Atomic Value)만을 가짐 (다중값/반복 그룹 제거)
-- 2. 2NF (제2정규형): 기본키가 단일 컬럼(IDENTITY)으로 구성되어 부분 함수 종속이 존재하지 않음
-- 3. 3NF (제3정규형): 이행적 함수 종속성을 제거하기 위해 카테고리, 회원, 도서, 대여 테이블을 각각 분리함
-- ============================================================

-- [기존 테이블 초기화]
-- 반복 실행 및 재테스트 시 에러 방지를 위해 기존 테이블을 역순으로 삭제합니다.
-- CASCADE 옵션은 FK로 엮인 연관 제약조건을 함께 해제합니다.
DROP TABLE IF EXISTS rental CASCADE;
DROP TABLE IF EXISTS book CASCADE;
DROP TABLE IF EXISTS member CASCADE;
DROP TABLE IF EXISTS category CASCADE;

-- ------------------------------------------------------------
-- 1. 카테고리 테이블 (category) - 부모 테이블
-- [정규화 근거 - 3NF 충족]:
-- 도서 테이블(book)에 카테고리명(category_name)을 직접 저장할 경우 발생할 수 있는
-- 이행적 함수 종속성(book_id -> category_id -> category_name)과 데이터 중복(갱신 이상)을
-- 방지하기 위해 별도 테이블로 분리함.
-- ------------------------------------------------------------

CREATE TABLE category (
    category_id INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY, -- 자동 증가 PK (표준 SQL)
    category_name VARCHAR(50) NOT NULL UNIQUE                 -- [제약조건] NOT NULL + UNIQUE
);


-- ------------------------------------------------------------
-- 2. 회원 테이블 (member) - 부모 테이블
-- [정규화 근거 - 1NF/2NF/3NF 충족]:
-- 회원의 기본 정보만 관리하며, 대여 기록(rental)과 분리하여 1:N 관계를 형성함.
-- 다중값 속성(예: 대여목록 리스트)을 포함하지 않아 원자성을 유지(1NF)하며,
-- 모든 비주요 속성이 기본키(member_id)에만 완전/직접 종속됨(2NF, 3NF).
-- ------------------------------------------------------------

CREATE TABLE member (
    member_id INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    email VARCHAR(100) NOT NULL UNIQUE,                       -- [제약조건] UNIQUE (중복 이메일 방지)
    name VARCHAR(50) NOT NULL,                                -- [제약조건] NOT NULL
    phone VARCHAR(20),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);


-- ------------------------------------------------------------
-- 3. 도서 테이블 (book) - 자식 테이블 (category 참조)
-- [정규화 근거 - 3NF 충족]:
-- category_id 외래키(FK)만을 참조하도록 설계하여, 카테고리명이 변경되더라도 
-- 도서 테이블의 수정 없이 카테고리 테이블만 수정하면 되는 이상 현상(Anomaly) 방지 구조를 갖춤.
-- ------------------------------------------------------------

CREATE TABLE book (
    book_id INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    title VARCHAR(150) NOT NULL,                              -- [제약조건] NOT NULL
    author VARCHAR(100) NOT NULL,
    price INT NOT NULL,
    category_id INT NOT NULL,                                 -- FK 컬럼
    CONSTRAINT fk_book_category FOREIGN KEY (category_id) REFERENCES category(category_id)
);


-- ------------------------------------------------------------
-- 4. 대여 기록 테이블 (rental) - 자식 테이블 (member, book 참조)
-- [정규화 근거 - 1NF/3NF 충족]:
-- 한 회원이 여러 도서를 대여하거나, 한 도서가 여러 번 대여되는 N:M 관계를 해소하기 위해
-- 대여 행위 자체를 주체로 하는 교차(대여) 테이블로 분리함.
-- member와 book의 비주요 정보(회원명, 도서가격 등)를 중복 저장하지 않고 
-- 외래키(FK)만 참조함으로써 이행적 함수 종속을 완전 제거(3NF)함.
-- ------------------------------------------------------------

CREATE TABLE rental (
    rental_id INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    member_id INT NOT NULL,                                   -- FK 1 컬럼
    book_id INT NOT NULL,                                     -- FK 2 컬럼
    rental_date DATE NOT NULL,                                -- 대여일
    return_date DATE,                                         -- 반납일 (대여 중이면 NULL)
    CONSTRAINT fk_rental_member FOREIGN KEY (member_id) REFERENCES member(member_id),
    CONSTRAINT fk_rental_book FOREIGN KEY (book_id) REFERENCES book(book_id)
);