#  Mini Git Simulation System

파이썬 기반으로 Git의 핵심 동작 방식(INIT, Commit, Branch, DAG 이력 관리, 최단 경로 탐색, 역색인 검색 등)을 시뮬레이션하는 CLI 프로그램입니다.

---

## 📂 1. 프로젝트 파일 구조 (Directory Structure)

```text
.
├── main.py              # CLI 진입점 및 명령어 파싱
├── commands.py          # GitCommandHandler (비즈니스 로직)
├── models.py            # MiniGitRepository 저장소, Commit 객체 구조 정의
├── algorithms.py        # Merge Sort, BFS 경로 탐색, 위상정렬
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
| **SWITCH**| `CHECKOUT <branch_name>` | `head_branch` 이동 |
| **LOG** | `LOG` | 현재 브랜치의 커밋 히스토리 출력 |
| **SEARCH** | `SEARCH "keyword"`<br>`SEARCH --author="name"` | 역색인 기반 커밋 검색 |
| **PATH** | `PATH <start_hash> <end_hash>` | 두 커밋 간 최단 경로 탐색 |
| **ANCESTORS** | `ANCESTORS <commit_hash>` | 해당 커밋에서 도달 가능한 모든 조상 커밋을 출력 |
| **EXIT** | `EXIT` | 프로그램 종료 |

### 2.3 Quick Start Scenario

```bash
# 1. 저장소 초기화 (필수)
[NO-REPO] > INIT Alice
Initialized empty Mini Git repository for user 'Alice'

# 2. 커밋 생성
[main] > COMMIT "Initial commit"
[c1] Committed successfully: "Initial commit"

# 3. 브랜치 생성 및 전환
[main] > BRANCH feature-a
Branch 'feature-a' created.
[main] > SWITCH feature-a
Switched to branch 'feature-a'

# 4. 신규 브랜치에서 커밋 추가 및 키워드로 검색
[feature-a] > COMMIT "Fix bug in search engine" --author="Bob"
[c2] Committed successfully: "Fix bug in search engine"
[feature-a] > SEARCH bug
[c2] Alice | 2026-07-27 15:21:03 | Fix bug in search engine

# 5. 현재 모든 브랜치의 커밋 로그를 부모순으로 정렬해 출력
[feature-a] > LOG
[c1] Alice | 2026-07-29 13:47:03 | Initial commit
[c2] Alice | 2026-07-29 13:47:36 | Fix bug in search engine

# 6. 해당 커밋에서 도달 가능한 모든 조상 커밋을 출력
[feature-a] > ANCESTORS c2
[c1] Alice | 2026-07-29 13:47:03 | Initial commit
```

---

## 📐 3. 핵심 시스템 명세 및 보완 사항

---

### 3.1 저장소 초기화 및 기본 브랜치 (`main`)

* **INIT 명령 필수화**: 시스템 시작 시 저장소 상태는 비활성화(`is_initialized = False`)되어 있으며, `INIT` 명령어를 실행하기 전에 타 명령어 호출 시 `"Run 'INIT' first"` 안내 후 동작을 차단합니다.
* **기본 브랜치 고정 (`main`)**: 초기화 시 기본 브랜치는 `main`으로 지정되며, Modern Git 컨벤션을 준수합니다.

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
* **get_topological_sort 동률(같은 진입 차수) 발생 시 처리**: 진입 차수가 0인 노드가 2개 이상일 경우, merge_sort 정렬을 수행합니다.

---

### 3.4 BFS 최단 경로 탐색 및 동률 경로 선택 규칙

* **동률 경로 선택 규칙 (문자열 조인 방식)**:
  1. 복수 최단 경로를 `->` 구분자로 연결하여 문자열로 변환합니다. (예: `"c1->c2->c4"`, `"c1->c3->c4"`)
  2. 사전순 비교(`path_A < path_B`)를 통해 가장 작은 문자열을 가진 경로를 선택하여 결과의 **결정론적(Deterministic) 보장**을 달성합니다.


### 3.5 역색인(Inverted Index) 및 토큰화 정규화 규칙

텍스트의 공백을 제거하고 소문자로 정규화하고 특수문자 제거
```
tokens = text.lower().split()
return [t.strip(",.?!\"'") for t in tokens if t.strip(",.?!\"'")]
```

### 🔍 역색인(Inverted Index) 복잡도 분석 (Complexity Analysis)

저장소 내 전체 커밋 수 $N$, 커밋 메시지의 평균 단어 수 $M$, 전체 단어/작성자 키워드의 총 가짓수 $K$라 할 때 역색인 구조의 복잡도는 다음과 같습니다.

#### 1. 시간 복잡도 (Time Complexity)
* **인덱스 빌드 (Build / Update): $O(N \cdot M)$**
  * 각 커밋 생성 시 메시지를 토큰화(Tokenization) 및 정규화(`.split()`, `.lower()`)하여 해시 테이블(Dict/Set)에 매핑합니다.
  * 커밋 $1$개당 평균 $M$개의 키워드가 추출되므로 전체 $N$개 커밋에 대해 $O(N \cdot M)$의 시간이 소요됩니다.
* **키워드/작성자 검색 (Search): $O(1)$**
  * 정규화된 쿼리 키워드로 해시 테이블을 조회하므로 **평균 $O(1)$** 시간에 해당 키워드를 포함하는 커밋 해시 집합(`Set`)을 추출합니다. (단, 검색 결과 커밋 목록을 해시 사전순으로 정렬하는 과정에서 $O(R \log R)$ 소요, $R$은 매칭된 커밋 수)

#### 2. 공간/메모리 복잡도 (Space Complexity)
* **메모리 비용: $O(K + N \cdot M)$**
  * `index_keyword` 및 `index_author` 딕셔너리에 저장되는 고유 키워드 수 $K$와, 각 키워드가 가리키는 커밋 해시 참조의 총 개수 $N \cdot M$에 비례합니다.
  * 파이썬의 `Set` 구조를 활용하여 중복 참조를 제거하고, 커밋 객체 전체가 아닌 **해시 문자열(Pointer)만 인덱싱**함으로써 메모리 오버헤드를 최적화했습니다.

---

### 3.6 대규모 데이터 확장 시 병목 분석 및 개선 제안

* **병목**: 대규모 검색 결과 정렬 지연.
* **개선 방안**: 최소힙을 통해 화면에 출력하고자 하는 커밋 개수를 제한하는 식으로 연산량을 줄임.

