# Mini Redis (Python CLI 기반 메모리 캐시 저장소)

학습 및 테스트 목적으로 파이썬의 내장 컬렉션(`dict`, `set` 등)을 전혀 사용하지 않고, 오직 표준 자료구조들을 직접 바닥부터 구현하여 빌드한 **Redis 스타일의 CLI 캐시 저장소**입니다. 

단일 스레드 REPL 환경에서 구동되며, 데이터 저장/조회뿐만 아니라 **LRU 기반 메모리 퇴거(Eviction)** 및 **최소 힙(Min-Heap) 기반의 TTL 만료 관리** 기능을 제공합니다.

---

## 🚀 주요 특징 (Key Architecture)

1. **내장 딕셔너리(`dict`) 금지**: 학습 목적으로 파이썬 내장 해시맵을 쓰지 않고 직접 링크드 리스트와 체이닝 기반 해시맵을 설계했습니다.
2. **O(1) 성능의 LRU 캐시**: 이중 연결 리스트를 활용하여 데이터 접근 시 즉시 최신 위치로 이동시키며, 메모리 한계 도달 시 가장 오래된 데이터를 즉시 탐색/제거합니다.
3. **Lazy Deletion 전략의 TTL**: 최소 힙(Min-Heap) 자료구조를 독립적으로 구현하여 만료 시간이 가장 임박한 데이터를 추적하며, 단일 스레드 제약 조건에 맞추어 명령 실행 직전에 만료 여부를 판별해 리소스를 해제합니다.
4. **따옴표 보존 인자 파서**: 공백을 기준으로 명령어를 파싱하되, 큰따옴표(`" "`) 내부의 공백은 문자열 데이터로 안전하게 보존하는 커스텀 파서를 포함합니다.

---

## 🛠 자료구조 설계 (Core Data Structures)

본 프로그램은 제약사항에 따라 각 자료구조가 독립된 모듈로 분리되어 있습니다.

### 1. 이중 연결 리스트 (Doubly Linked List)
* **구조**: `prev`, `next`, `data(key, value)` 필드를 가진 노드 구조
* **특징**: 모든 삽입, 삭제, 맨 앞으로 이동(`move_to_front`) 연산이 **$O(1)$**의 시간 복잡도로 작동하여 LRU 알고리즘의 핵심 엔진 역할을 합니다.

### 2. 해시맵 (HashMap - 체이닝 방식)
* **구조**: 고정 길이 배열과 직접 설계한 해시 함수 활용
* **충돌 해결**: 이중 연결 리스트를 재사용하여 체이닝(Chaining) 방식으로 해결
* **동적 확장**: 로드 팩터(Load Factor)가 **0.75(75%)**를 초과할 경우, 자동으로 버킷 배열을 **2배 확장(Resize)**하고 기존 엔트리들을 재해싱(Re-hashing)하여 적재합니다.

### 3. 최소 힙 (Min-Heap)
* **구조**: 이진 트리 기반 배열 구조
* **특징**: 원소 삽입 시 위로 정렬하는 `_heapify_up`, 추출 시 아래로 정렬하는 `_heapify_down` 구조가 완벽히 독립 구현되어 있으며, `(expire_at, key)` 형태의 요소를 받아 만료 순위를 정교하게 관리합니다.

---

## 💻 지원 명령어 (Supported Commands)

### String 기본 명령어
* `SET key value`: 키에 값을 저장합니다. (기존 키 존재 시 TTL 초기화 및 값 업데이트, LRU 순위 갱신)
* `GET key`: 키의 값을 조회합니다. (조회 성공 시 LRU 갱신, 만료된 키라면 조회 전 자동 삭제 후 `(nil)` 반환)
* `DEL key`: 키를 삭제하며 해시맵, LRU, TTL 힙 구조 전반에서 리소스를 일괄 제거합니다.
* `EXISTS key`: 키의 존재 여부를 확인합니다. (`(integer) 1` 또는 `0`)
* `DBSIZE`: 만료된 데이터를 사전에 정제한 후, 현재 유효한 총 키 개수를 반환합니다.
* `KEYS`: 유효한 전체 키 목록을 Redis 스타일 번호 매기기 형태로 정렬하여 출력합니다.

### 메모리 관리 명령어
* `CONFIG SET maxmemory <bytes>`: 최대 메모리 제한을 바이트 단위로 설정합니다. (`0`은 무제한)
* `INFO memory`: 현재 사용량(`used_memory`), 제한량, 용량 초과로 인해 쫓겨난 키 개수(`evicted_keys`)를 확인합니다.
  * *used_memory 산정 공식*: `Σ(len(key) + len(value))` (자료구조 오버헤드 제외)
  * *LRU 퇴거 규칙*: 제한량 초과 시, 용량이 한도 이하가 될 때까지 가장 오래 사용되지 않은 키부터 강제 퇴거시킵니다.

### TTL 관리 명령어
* `EXPIRE key seconds`: 특정 키에 만료 시간(초 단위)을 설정하여 최소 힙에 예약 등록합니다.
* `TTL key`: 만료까지 남은 시간을 초 단위 숫자로 조회합니다. (만료 시간 없음: `-1`, 키 없음: `-2`)

---

## 🏃‍♂️ 실행 방법 (Usage)

프로그램은 별도의 네트워크 통신 없이 로컬 터미널 REPL 인터페이스로 구동됩니다.

```bash
python main.py
```
## 실행 예시
mini-redis> SET user:1 "Alice Kim"   
OK  
mini-redis> EXPIRE user:1 60  
(integer) 1  
mini-redis> TTL user:1  
(integer) 56  
mini-redis> CONFIG SET maxmemory 10  
OK  
mini-redis> SET user:2 "Bob"  
(error) OOM command not allowed when used_memory > 'maxmemory'  
mini-redis> EXIT  

## 에러 처리 표준 (Error Handling)
잘못된 명령: (error) ERR unknown command '<cmd>'

인자 개수 오류: (error) ERR wrong number of arguments for '<cmd>' command

정수 파싱 실패: (error) ERR value is not an integer or out of range

메모리 초과(OOM): (error) OOM command not allowed when used_memory > 'maxmemory'