#  Mini Git Simulation System

파이썬 기반으로 Git의 핵심 동작 방식(INIT, Commit, Branch, DAG 이력 관리, 최단 경로 탐색, 역색인 검색 등)을 시뮬레이션하는 CLI 프로그램입니다.

---

## 📂 1. 프로젝트 파일 구조 (Directory Structure)

```text
.
├── main.py              # CLI 진입점 및 명령어 파싱/루프
├── repo_handler.py      # GitCommandHandler (비즈니스 로직 및 예외 제어)
├── models.py            # MiniGitRepository, Commit 데이터 모델
├── utils.py             # Merge Sort, BFS 경로 탐색, 토큰화 유틸리티
├── tests/
│   └── test_system.py   # 유닛 테스트 (초기화 조건, 정렬 안정성, 동률 경로)
└── README.md            # 기술 명세서
```

---

## 🛠️ 2. 실행 방법 및 명령어 안내 (Usage)

### 2.1 프로그램 실행
```bash
python main.py
```

### 2.2 지원 명령어 목록 (Commands)

| 명령어 | 형식 및 예시 | 설명 |
| :--- | :--- | :--- |
| **INIT** | `INIT [<user_name>]` | 저장소 초기화 (미입력 시 기본 사용자 'User') |
| **COMMIT** | `COMMIT "message" [--author="name"]` | 커밋 생성 및 `head_branch` 이동 |
| **BRANCH** | `BRANCH <branch_name>` | 브랜치 생성 |
| **CHECKOUT**| `CHECKOUT <branch_name>` | `head_branch` 이동 |
| **LOG** | `LOG` | 현재 브랜치의 커밋 히스토리 출력 |
| **SEARCH** | `SEARCH "keyword"`<br>`SEARCH --author="name"` | 역색인 기반 커밋 검색 |
| **PATH** | `PATH <start_hash> <end_hash>` | 두 커밋 간 최단 경로 탐색 |
| **HELP** | `HELP` | 도움말 출력 |
| **EXIT** | `EXIT` | 프로그램 종료 |

### 2.3 Quick Start Scenario

```bash
# 1. 저장소 초기화 (필수)
[NO-REPO] > INIT Alice
Initialized empty Mini Git repository for user 'Alice' in branch 'main'.

# 2. 커밋 생성
[main] > COMMIT "Initial commit"
[main c1] Initial commit

# 3. 브랜치 생성 및 전환
[main] > BRANCH feature-a
Branch 'feature-a' created at c1.
[main] > CHECKOUT feature-a
Switched to branch 'feature-a'.

# 4. 신규 브랜치에서 작업 및 검색
[feature-a] > COMMIT "Fix bug in search engine" --author="Bob"
[feature-a c2] Fix bug in search engine
[feature-a] > SEARCH bug
[c2] Fix bug in search engine (Author: Bob, Parents: c1)
```

---

## 📐 3. 핵심 시스템 명세 및 보완 사항

---

### 3.1 저장소 초기화 및 기본 브랜치 (`main`)

* **INIT 명령 필수화**: 시스템 시작 시 저장소 상태는 비활성화(`is_initialized = False`)되어 있으며, `INIT` 명령어를 실행하기 전에 타 명령어 호출 시 `"Run 'INIT' first"` 안내 후 동작을 차단합니다.
* **기본 브랜치 고정 (`main`)**: 초기화 시 기본 브랜치는 `main`으로 지정되며, Modern Git 컨벤션을 준수합니다.
* **HEAD 포인터 불변식 (Invariants)**:
  $$\text{head\_branch} \in \text{Keys}(\text{branches}) \quad \land \quad \text{branches}[\text{head\_branch}] \in \text{commits}$$
  `head_branch` 포인터는 커밋 해시를 직접 가리키지 않고 **항상 브랜치를 경유**합니다.

---

### 3.2 DAG (Directed Acyclic Graph) 구조 명세

* **왜 DAG이어야 하는가?**
  * **이력 불변성(Immutability)**: 이전 커밋은 다음 커밋의 부모(Parent)가 되며 시간축은 한 방향으로만 흐릅니다.
  * **무결성 보장**: 이전 상태를 참조하여 쌓아 올리므로 데이터를 보호합니다.
* **사이클(Cycle) 발생 시 문제점**: 위상 정렬 및 BFS 경로 탐색 시 무한 루프에 빠지며 인과관계가 붕괴됩니다.

---

### 3.3 정렬 알고리즘 및 위상 정렬 (`merge_sort`)

* **병합 정렬 (`merge_sort`) 복잡도 및 안정성**:
  * **시간 복잡도**: $O(N \log N)$ (최악, 최선, 평균 동일)
  * **공간 복잡도**: $O(N)$
  * **안정성 (Stability)**: Stable Sort (동률 키 값 발생 시 상대적 순서 보장)
* **동률(같은 진입 차수) 발생 시 처리 방식**: 진입 차수가 0인 노드가 2개 이상일 경우, 해시 문자열 비교(`queue[i] > queue[j]`)를 통해 사전순 정렬을 수행합니다.

---

### 3.4 BFS 최단 경로 탐색 및 동률 경로 선택 규칙

* **동률 경로 선택 규칙 (문자열 조인 방식)**:
  1. 복수 최단 경로를 `->` 구분자로 연결하여 문자열로 변환합니다. (예: `"c1->c2->c4"`, `"c1->c3->c4"`)
  2. 사전순 비교(`path_A < path_B`)를 통해 가장 작은 문자열을 가진 경로를 선택하여 결과의 **결정론적(Deterministic) 보장**을 달성합니다.

---

### 3.5 해시 생성 전략 및 Trade-off

| 구분 | 순차 카운터 방식 (현재 적용) | Cryptographic (SHA-256) |
| :--- | :--- | :--- |
| **재현성 (Reproducibility)** | **매우 높음** (항상 순서 보장) | 낮음 |
| **테스트 용이성** | **극상** (직관적 검증) | 보통 |
| **충돌 위험도** | 없음 ($O(1)$ 카운터) | 극히 낮음 |
| **보안성** | 낮음 | 높음 |

---

### 3.6 역색인(Inverted Index) 및 토큰화 정규화 규칙

* **토큰화 파싱**: `r'(?:[^\s"]+|"[^"]*")'` (공백 단위로 쪼개되 쌍따옴표 내부 공백은 단일 토큰으로 보존)
* **정규화**: `.strip('"')` 수행 후 `.lower()`로 표준화하여 대소문자 구분 없이 $O(1)$ 조회를 지원합니다.

---

### 3.7 대규모 데이터 확장 시 병목 분석 및 개선 제안

* **병목 후보**: 전체 커밋 RAM 상주로 인한 메모리 오버헤드, 대규모 검색 결과 정렬 지연.
* **개선 방안**: Embedded KV DB(RocksDB) 영속화, Priority Queue를 활용한 Top-K 부분 정렬, LRU Cache 도입.

