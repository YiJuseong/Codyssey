-- ============================================================
-- 과제 제출물 #3: 핵심 SQL 쿼리 15개 스크립트 (03_queries.sql)
-- DBMS: PostgreSQL 16+
-- ============================================================

-- ============================================================
-- [범주 1: 기본 조회 - 4개]
-- ============================================================

-- Q1. [기본 조회 1] 도서 가격이 20,000원 이상인 도서 목록 조회 (WHERE 조건 사용)
SELECT * 
FROM book 
WHERE price >= 20000;


-- Q2. [기본 조회 2] 도서 목록을 가격이 비싼 순서(내림차순)로 정렬하여 조회 (ORDER BY 사용)
SELECT title, author, price 
FROM book 
ORDER BY price DESC;


-- Q3. [기본 조회 3] 가장 최근에 가입한 회원 3명의 정보를 조회 (ORDER BY, LIMIT 사용)
SELECT member_id, name, email, created_at 
FROM member 
ORDER BY created_at DESC 
LIMIT 3;


-- Q4. [기본 조회 4] 현재 반납되지 않은(대여 중인) 대여 기록 목록 조회 (WHERE ... IS NULL 사용)
SELECT * 
FROM rental 
WHERE return_date IS NULL;



-- ============================================================
-- [범주 2: 조인(JOIN) - 4개]
-- ============================================================

-- Q5. [조인 1: INNER JOIN] 대여 기록과 회원의 이름을 결합하여 누구 대여 기록인지 조회
SELECT r.rental_id, m.name AS member_name, r.book_id, r.rental_date, r.return_date
FROM rental r
INNER JOIN member m ON r.member_id = m.member_id;


-- Q6. [조인 2: INNER JOIN] 도서의 제목과 해당 도서가 속한 카테고리명을 결합하여 조회
SELECT b.book_id, b.title, b.author, c.category_name
FROM book b
INNER JOIN category c ON b.category_id = c.category_id;


-- Q7. [조인 3: INNER JOIN] 대여 기록별 회원이름, 도서제목, 대여일자를 3개 테이블 조인으로 조회
SELECT r.rental_id, m.name AS member_name, b.title AS book_title, r.rental_date
FROM rental r
INNER JOIN member m ON r.member_id = m.member_id
INNER JOIN book b ON r.book_id = b.book_id;


-- Q8. [조인 4: LEFT JOIN] 전체 도서 목록과 대여 이력을 함께 조회 (대여 이력이 없는 도서도 포함)
SELECT b.book_id, b.title, r.rental_id, r.rental_date
FROM book b
LEFT JOIN rental r ON b.book_id = r.book_id;



-- ============================================================
-- [범주 3: 집계(AGGREGATE) - 3개]
-- ============================================================

-- Q9. [집계 1: COUNT + GROUP BY] 카테고리별로 등록된 도서의 총 개수를 조회
SELECT category_id, COUNT(*) AS book_count
FROM book
GROUP BY category_id
ORDER BY category_id;


-- Q10. [집계 2: AVG + GROUP BY] 카테고리별 도서의 평균 가격을 소수점 둘째자리까지 반올림하여 조회
SELECT category_id, ROUND(AVG(price), 2) AS avg_price
FROM book
GROUP BY category_id;


-- Q11. [집계 3: SUM + GROUP BY] 회원별로 지금까지 대여한 도서들의 총 가격 합계를 조회
SELECT r.member_id, m.name AS member_name, SUM(b.price) AS total_rented_price
FROM rental r
INNER JOIN member m ON r.member_id = m.member_id
INNER JOIN book b ON r.book_id = b.book_id
GROUP BY r.member_id, m.name;



-- ============================================================
-- [범주 4: 서브쿼리(SUBQUERY) - 1개]
-- ============================================================

-- Q12. [서브쿼리] 전체 도서의 평균 가격보다 더 비싼 도서의 목록을 조회
SELECT book_id, title, price
FROM book
WHERE price > (SELECT AVG(price) FROM book);



-- ============================================================
-- [범주 5: 데이터 수정 및 삭제 - 2개]
-- ============================================================

-- Q13. [데이터 수정] 회원 '김철수'의 전화번호 정보 변경 (UPDATE)
UPDATE member
SET phone = '010-9999-8888'
WHERE name = '김철수';


-- Q14. [데이터 삭제] 대여 기록 중 1번 대여 건(rental_id = 1) 삭제 (DELETE)
DELETE FROM rental
WHERE rental_id = 1;



-- ============================================================
-- [범주 6: 인덱스(INDEX) - 1개]
-- ============================================================

-- Q15. [인덱스 생성] 도서 제목(title)을 이용한 검색 연산 성능을 향상시키기 위해 인덱스 생성
-- 적용 이유: 서비스 특성상 도서 제목을 키워드로 검색하는 WHERE title = '...' 쿼리가 자주 발생하므로, 전체 테이블 스캔(Full Scan) 방지를 위해 인덱스를 적용함.
CREATE INDEX idx_book_title ON book(title);