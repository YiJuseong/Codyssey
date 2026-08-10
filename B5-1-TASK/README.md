#  도서 대여 데이터베이스 구축 및 SQL 분석 프로젝트 보고서

본 프로젝트는 백엔드 프레임워크 없이 **PostgreSQL**과 **DBeaver**를 활용하여 도서 대여 도메인의 데이터베이스를 설계하고, 정규화된 스키마 구축 및 핵심 SQL 쿼리 15개를 통한 데이터 분석을 수행한 프로젝트입니다.

---

## 🛠️ 개발 및 실습 환경

- **DBMS**: PostgreSQL 18.4
- **Database Tool**: DBeaver Community
- **Container Environment**: macOS + OrbStack (Docker Engine)
- **Language**: Standard SQL (PostgreSQL Syntax)

---

## 1. DB vs Excel 비교 (관계 저장 및 무결성 차이)

데이터를 저장하고 관리할 때 **관계형 데이터베이스(RDBMS)**와 **스프레드시트(Excel)**는 구조와 목적에서 다음과 같은 근본적인 차이가 있습니다.

| 구분 | RDBMS (PostgreSQL) | Spreadsheet (Excel) |
| :--- | :--- | :--- |
| **관계 저장 (Relationship)** | **외래키(FK, Foreign Key)** 제약조건을 통해 테이블 간의 1:N, N:M 연관관계를 물리적으로 연결하고 참조 무결성을 보장함. | 별도의 물리적 관계가 없으며, `VLOOKUP`이나 `XLOOKUP` 등의 함수로 시트 간 데이터를 임시 매핑함. |
| **데이터 무결성 (Integrity)** | 스키마 정의 시 **PK, FK, NOT NULL, UNIQUE** 등의 제약조건을 강제하여 오입력, 중복, 부모 없는 자식 데이터 생성을 엔진 차원에서 차단함. | 셀 단위로 자유롭게 수정이 가능하여 데이터 타입 불일치, 오탈자, 중복값 입력 등 데이터 오염에 매우 취약함. |
| **동시성 및 대용량** | **ACID 트랜잭션**을 지원하여 수많은 사용자가 동시에 읽기/쓰기를 수행해도 데이터 일관성을 유지하며, 수백만 건 이상의 대용량 데이터 처리 가능. | 파일 단위 락(Lock) 구조로 동시 편집에 제한이 있고, 행 수 제한(1,048,576행) 및 대용량 처리 시 성능 저하가 심함. |
| **데이터 변경 영향 (Anomaly)** | 정규화를 통해 데이터가 단 한 곳에만 존재하므로, 수정 시 해당 원본 테이블만 변경하면 연관된 모든 조회에 반영됨 (갱신 이상 없음). | 동일한 데이터가 여러 시트에 중복 작성된 경우가 많아 수정 시 누락이나 불일치가 발생할 위험이 높음. |

---

## 2. 테이블 정규화(Normal Form) 설계 근거

본 데이터베이스는 **이상 현상(Anomaly)을 방지하고 데이터 중복을 최소화**하기 위해 **제3정규형(3NF)**까지 충족하도록 설계되었습니다.

### 1NF (제1정규형): 원자값 보장
- **적용**: 모든 테이블의 컬럼은 다중값(List, Array)이나 반복 그룹을 가지지 않고 하나의 원자값(Atomic Value)만 저장합니다.
- **예시**: `member` 테이블에 `rented_books`와 같은 컬럼을 두어 대여 목록을 콤마(`,`)로 저장하지 않고, `rental`이라는 교차 테이블로 분리함.

### 2NF (제2정규형): 부분 함수 종속성 제거
- **적용**: 모든 테이블의 기본키(PK)가 단일 컬럼(`GENERATED ALWAYS AS IDENTITY`)으로 구성되어 있어, 기본키의 일부에만 종속되는 부분 함수 종속이 존재하지 않습니다.

### 3NF (제3정규형): 이행적 함수 종속성 제거
- **적용**: 기본키(PK)가 아닌 일반 컬럼이 다른 일반 컬럼을 결정하는 이행적 종속을 제거했습니다.
- **분리 근거**:
  - `book` 테이블에 카테고리명(`category_name`)을 직접 저장하면 `book_id -> category_id -> category_name` 구조의 이행적 종속이 발생합니다. 카테고리명이 변경될 때 수많은 도서 데이터가 수정되는 갱신 이상을 막기 위해 **`category` 테이블을 별도로 분리**하였습니다.
  - `rental` 테이블은 N:M 관계를 해소하는 대여 행위 중심의 교차 테이블로, 회원명(`name`)이나 도서가격(`price`)을 중복 저장하지 않고 **`member_id`, `book_id` 외래키(FK)만 참조**합니다.

---

## 3. 컬럼 데이터 타입 선택 이유

의미에 맞는 정확한 데이터 타입 선택은 **메모리 절약, 데이터 무결성 유지, 조회 성능 최적화**의 기반이 됩니다.

| 테이블 | 컬럼명 | 데이터 타입 | 선택 이유 및 서술 |
| :--- | :--- | :--- | :--- |
| **공통** | `*_id` | `INT + IDENTITY` | 식별용 PK/FK 컬럼으로, 정수형을 사용하여 인덱스 검색 및 조인 연산 속도를 극대화함. |
| **category** | `category_name` | `VARCHAR(50)` | 길이가 가변적인 짧은 문자열이며, `NOT NULL`과 `UNIQUE`를 통해 중복 입력을 차단함. |
| **member** | `email` | `VARCHAR(100)` | 이메일 주소는 가변 길이가 크므로 충분한 공간을 확보하되 `UNIQUE` 제약으로 식별성을 보장함. |
| **member** | `phone` | `VARCHAR(20)` | 전화번호는 숫자 계산 대상이 아니며, 맨 앞의 `0` 보존 및 하이픈(`-`) 기호 저장을 위해 `INT`가 아닌 `VARCHAR` 선택. |
| **member** | `created_at` | `TIMESTAMP` | 회원 가입 시점의 날짜뿐만 아니라 상세 시/분/초 시각 정보까지 정확히 기록하기 위해 적용. |
| **book** | `price` | `INT` | 도서 가격은 소수점이 필요 없는 원화(KRW) 정수 데이터이며, `SUM`, `AVG` 등 수학적 집계 연산을 수행하기 위해 선택. |
| **rental** | `rental_date`<br>`return_date` | `DATE` | 대여 및 반납 시 시/분/초 정보는 불필요하고 '일자' 정보만 요구되므로 `TIMESTAMP` 대신 `DATE` 선택. `return_date`는 미반납(대여 중) 상태 표현을 위해 `NULL` 허용. |

---

## 4. INNER JOIN vs LEFT JOIN 차이점

두 조인은 테이블 간 관계를 맺어 조회할 때 **일치하지 않는 행(Unmatched Rows)을 처리하는 방식**에서 결정적인 차이가 있습니다.

```text
[INNER JOIN] : 양쪽 테이블에 모두 존재하는 교집합 데이터만 추출
[LEFT JOIN]  : 왼쪽 테이블의 모든 데이터 + 오른쪽에 일치하는 데이터 (없으면 NULL)
```

1. **`INNER JOIN` (내부 조인)**
   - 조인 조건(`ON`)을 만족하는 **양쪽 테이블의 교집합 데이터만 반환**합니다.
   - *예시 (Q5, Q7)*: 대여 기록(`rental`)이 실제로 존재하는 회원과 도서 정보만 조회됩니다. 대여를 한 번도 하지 않은 회원은 결과에서 제외됩니다.

2. **`LEFT JOIN` (외부 조인)**
   - **왼쪽(기준) 테이블의 모든 행을 유지**하고, 오른쪽 테이블에서 조건에 맞는 데이터를 가져옵니다. 조건에 맞는 오른쪽 데이터가 없으면 `NULL`로 채웁니다.
   - *예시 (Q8)*: 대여된 적이 단 한 번도 없는 도서를 포함하여 **'전체 도서 목록'**을 확인하고 싶을 때 사용합니다. 대여 이력이 없는 도서의 대여 관련 컬럼은 `NULL`로 표시됩니다.

---

## 5. 🔍 복잡 쿼리 단계별 분해 및 로직 설명

작성된 15개 핵심 쿼리 중 복합적인 연산이 포함된 주요 쿼리 3개의 내부 실행 로직을 단계별로 분해하여 설명합니다.

### 📌 Q7. 3개 테이블 다중 조인 (INNER JOIN)
> **쿼리**: 대여 기록별 회원이름, 도서제목, 대여일자를 3개 테이블 조인으로 조회

```sql
SELECT r.rental_id, m.name AS member_name, b.title AS book_title, r.rental_date
FROM rental r
INNER JOIN member m ON r.member_id = m.member_id
INNER JOIN book b ON r.book_id = b.book_id;
```
- **단계별 실행 로직**:
  1. **`FROM rental r`**: 기준이 되는 대여 기록 테이블(`rental`)을 불러옵니다.
  2. **`INNER JOIN member m ON ...`**: `rental`의 `member_id`와 `member`의 `member_id`가 일치하는 행을 결합하여 대여자의 이름(`name`) 정보를 획득합니다.
  3. **`INNER JOIN book b ON ...`**: 결합된 결과에 `rental`의 `book_id`와 `book`의 `book_id`가 일치하는 행을 2차 결합하여 대여된 도서 제목(`title`) 정보를 획득합니다.
  4. **`SELECT ...`**: 최종 결합된 데이터 집합에서 필요한 컬럼(`rental_id`, `member_name`, `book_title`, `rental_date`)만 추출하여 출력합니다.

---

### 📌 Q11. 조인 + 집계 함수 + 그룹화 (SUM + GROUP BY + JOIN)
> **쿼리**: 회원별로 지금까지 대여한 도서들의 총 가격 합계를 조회

```sql
SELECT r.member_id, m.name AS member_name, SUM(b.price) AS total_rented_price
FROM rental r
INNER JOIN member m ON r.member_id = m.member_id
INNER JOIN book b ON r.book_id = b.book_id
GROUP BY r.member_id, m.name;
```
- **단계별 실행 로직**:
  1. **`FROM ... JOIN`**: `rental`, `member`, `book` 3개 테이블을 조인하여 [대여한 회원 ID, 회원 이름, 대여한 도서 가격]을 한 행으로 만드는 평탄화 작업을 수행합니다.
  2. **`GROUP BY r.member_id, m.name`**: 동일한 회원(`member_id`, `name`)을 기준으로 결과 집합을 그룹(Group)으로 묶습니다.
  3. **`SUM(b.price)`**: 각 회원 그룹 내에 속한 도서들의 `price` 컬럼 값들을 모두 합산 연산합니다.
  4. **`SELECT`**: 회원 식별 정보와 계산된 총 대여 금액(`total_rented_price`)을 최종 반환합니다.

---

### 📌 Q12. 중첩 서브쿼리 (Subquery)
> **쿼리**: 전체 도서의 평균 가격보다 더 비싼 도서의 목록을 조회

```sql
SELECT book_id, title, price
FROM book
WHERE price > (SELECT AVG(price) FROM book);
```
- **단계별 실행 로직**:
  1. **서브쿼리(Subquery) 먼저 실행**: `(SELECT AVG(price) FROM book)` 가 단독으로 먼저 실행되어 전체 도서의 평균 가격(예: `21,830원`)이라는 **단일 값(Scalar Value)**을 계산합니다.
  2. **메인 쿼리(Main Query) 조건 비교**: 서브쿼리의 결과값이 메인 쿼리의 `WHERE` 조건절에 전달되어 `WHERE price > 21830` 문장으로 변환됩니다.
  3. **최종 필터링 및 출력**: `book` 테이블의 각 행을 순회하며 가격이 21,830원보다 높은 도서들만 필터링하여 출력합니다.

---

## 📁 제출물 파일 구성

```text
book_rental_assignment/
├── README.md             # 프로젝트 설계를 정리한 문서 (본 파일)
├── 01_schema.sql         # 스키마 생성 및 정규화/타입 근거 주석 파일
├── 02_data.sql           # 샘플 데이터 INSERT (각 테이블 10행 이상)
├── 03_queries.sql        # 핵심 SQL 쿼리 15개 스크립트
└── results/              # 쿼리별 실행 결과 캡처 이미지 폴더
    ├── q01_result.png
    ├── q02_result.png
    └── ... (q15까지)
```