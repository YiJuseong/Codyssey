# Git AI Assistant (Git 변경사항 기반 커밋 & PR 자동 생성 CLI)

Git 저장소의 변경 내역(`git status`, `git diff`)을 분석하여 컨벤션에 맞는 **커밋 메시지**와 구조화된 **Pull Request(PR) 초안**을 자동으로 생성해 주는 AI 개발 보조 CLI 도구입니다.

---

##  주요 기능

- **자동 변경사항 감지**: Staged(`git diff --cached`) 및 Unstaged(`git diff`) 코드 변경점을 자동으로 수집 및 감지합니다.
- **표준 커밋 메시지 생성 (`commit`)**: `타입: 제목` 형식과 2~4줄의 간결한 요약 본문을 작성합니다.
- **구조화된 PR 본문 생성 (`pr`)**: `Why`(배경), `What`(변경 내역), `How to Test`(검증 방법) 섹션으로 정돈된 리뷰용 문서를 생성합니다.
- **유연한 CLI 옵션**: 모델 변경(`--model`), 생성 온도(`--temperature`), 토큰 제한(`--max-tokens`) 등을 터미널 인자로 조정할 수 있습니다.

---

##  사전 요구사항

- **Python**: 3.9 이상
- **Git**: 로컬 환경에 Git이 설치 및 초기화되어 있어야 합니다.
- **Gemini API Key**: [Google AI Studio](https://aistudio.google.com/)에서 발급받은 API 키

---

## 🚀 설치 및 환경 설정

### 1. 리포지토리 클론 및 이동
```bash
git clone https://github.com/YiJuseong/Codyssey.git
cd Codyssey/b6-2-task
```

### 2. 가상환경 생성 및 활성화
독립된 패키지 환경을 위해 가상환경 생성을 강력히 권장합니다.

```bash
# 가상환경 생성
python3 -m venv venv

# 가상환경 활성화
# macOS / Linux:
source venv/bin/activate
# Windows (PowerShell):
.\venv\Scripts\Activate.ps1
```

### 3. 필수 패키지 설치
```bash
pip install -r requirements.txt
```

### 4. API Key 환경변수 설정
터미널 세션에 Gemini API Key를 등록합니다.

```bash
# macOS / Linux:
export GEMINI_API_KEY="your_actual_gemini_api_key_here"

# Windows (PowerShell):
$env:GEMINI_API_KEY="your_actual_gemini_api_key_here"
```

---

## 💻 사용 방법 및 실행 예시

### 1. 커밋 메시지 생성 (`commit`)
코드를 수정한 뒤(Staged 또는 Unstaged 상태) 아래 명령어를 실행합니다.

```bash
python main.py commit
```

**출력 결과 예시:**
```text
feat: 사용자 로그인 유효성 검사 로직 추가

- 이메일 형식 정규식 검증 로직 구현
- 비밀번호 8자리 이상 입력 제한 조건 추가
- 로그인 실패 시 노출할 에러 메시지 컴포넌트 연동
```

---

### 2. PR 초안 생성 (`pr`)
기능 구현 완료 후 PR 작성을 위한 초안을 생성합니다.

```bash
python main.py pr
```

**출력 결과 예시:**
```markdown
[Feature] 사용자 인증 및 로그인 폼 유효성 검사 구현

### Why
- 잘못된 형식의 계정 정보 입력으로 인한 백엔드 인증 에러를 사전에 방지하기 위함
- 로그인 실패 시 명확한 피드백을 제공하여 사용자 경험 개선

### What
- `validators.py`: 이메일/비밀번호 정규식 검증 함수 추가
- `LoginForm.vue`: 입력 실시간 유효성 피드백 UI 및 에러 모달 연동
- `api/auth.js`: 로그인 실패 상태 코드별 에러 핸들링 로직 추가

### How to Test
- 이메일 형식에 맞지 않는 값 입력 시 경고 문구 노출 확인
- 8자리 미만 비밀번호 입력 시 버튼 비활성화 동작 확인
- 잘못된 계정 정보 제출 시 에러 팝업 정상 노출 확인
```

---

### 3. CLI 옵션 활용

```bash
# 모델 변경 (기본값: gemini-3.6-flash)
python main.py commit --model gemini-1.5-flash

# 생성 온도 및 최대 토큰 수 조정
python main.py pr --temperature 0.3 --max-tokens 800

# 안전 모드 비활성화
python main.py commit --no-safe-mode
```

---

## Alias 등록

매번 프로젝트 폴더로 이동하지 않고, PC 내 어떤 Git 프로젝트에서든 바로 사용하려면 단축어를 등록하세요.

```bash
# ~/.zshrc 또는 ~/.bashrc 파일에 추가
alias git-ai="/절대경로/Codyssey/b6-2-task/venv/bin/python /절대경로/Codyssey/b6-2-task/main.py"

# 설정 적용
source ~/.zshrc
```

이제 어떤 Git 작업 폴더에서든 `git-ai commit`, `git-ai pr`로 즉시 실행할 수 있습니다.

---

##  주의사항 및 운영 가이드

1. **보안 및 개인정보 보호 (`.gitignore`)**
   - API 키가 포함된 `.env` 파일이나 로컬 가상환경 폴더(`venv/`)는 절대 원격 저장소에 커밋/푸시하지 마세요.
   - 대용량 파일이나 민감 정보(비밀번호, 토큰 등)가 포함된 변경점은 diff 생성 전 검토해야 합니다.
2. **API 사용량 및 Rate Limit**
   - 무료 티어 API 키 사용 시 분당 요청 수(RPM) 제한에 도달할 수 있으므로 과도한 반복 호출을 피해주세요.
---

##  AI 생성 결과물 검토 체크리스트 (Human-in-the-Loop)

본 도구가 생성한 커밋 메시지 및 PR 템플릿은 **초안(Draft)**이며, LLM의 특성상 환각(Hallucination), 편향, 누락이 발생할 수 있습니다. Git에 반영하거나 원격 저장소에 Push하기 전에 반드시 아래 항목을 검토하세요.

- [ ] **코드 변경점 일치 여부 (정확성)**
  - 실제 수정한 내용 외에 diff에 없는 가상의 기능이나 파일 변경이 설명에 포함되지 않았는가?
  - Breaking Change나 주요 로직 변경 사항이 누락되지 않았는가?
- [ ] **민감 정보 노출 여부 (보안)**
  - Safe Mode 적용 후에도 API Key, 비밀번호, 개인 식별 정보(이메일, 주민번호 등), 사내 인프라 IP 등이 본문에 그대로 노출되어 있지 않은가?
- [ ] **컨벤션 및 스타일 준수 (포맷)**
  - Conventional Commits 접두사(`feat:`, `fix:`, `refactor:` 등)가 변경 목적에 적절한가?
  - 제목 첫 글자 대소문자, 마침표 생략, 제목 글자 수(커밋: 50~72자, PR: 80자 이내) 제약을 만족하는가?
- [ ] **중립적 표현 및 편향 확인 (윤리/가독성)**
  - 주관적이거나 모호한 수식어, 편향된 단정적 표현 대신 사실에 기반한 명확한 기술 용어로 작성되었는가?

  ---

##  CLI 실행 옵션 설계 목적 및 재현성 가이드

본 도구는 핵심 생성 파라미터를 CLI 옵션(`argparse`)으로 노출하여 개발자의 **실험적 탐색(Exploration)**과 **결과 재현성(Reproducibility)**을 직접 제어할 수 있도록 설계되었습니다.

### 1. 주요 파라미터별 제어 목적

| 옵션 플래그 | 기본값 | 주요 목적 및 영향도 |
| :--- | :--- | :--- |
| `--model` | `gemini-3.6-flash` | **추론 품질과 지연 시간(Latency) 간의 실험**<br>- 경량 모델(`flash`)은 빠른 반응 속도와 비용 절감에 최적화<br>- 고성능 모델(`pro`)은 복잡하고 긴 diff의 심층 아키텍처 분석에 적합 |
| `--temperature` | `0.2` | **결과의 결정론적 재현성(Reproducibility) 제어**<br>- 낮은 값(0.0 ~ 0.2): 동일 diff 입력 시 일관된 컨벤션과 일정한 포맷 유지 (재현성 극대화)<br>- 높은 값(0.5 이상): 문맥 표현의 다양성이 커지나 출력 포맷 위반 가능성 증가 |
| `--max-tokens` | `500` | `--max-tokens`는 모델이 한 번의 응답에서 생성할 수 있는 최대 토큰(단어/형태소 단위) 상한을 설정합니다.

* **절단 위험(Truncation Risk)과 컨텍스트 유지**:
  * 값을 너무 낮게 설정하면 응답 생성 도중 상한에 도달해 **문장이 완성되지 못하고 중간에 끊기거나, PR 템플릿의 필수 마크다운 섹션·불릿 목록이 잘리는 현상(Truncation)**이 발생합니다.
  * 반대로 값을 지나치게 높게 잡으면 불필요한 서술이나 장황한 설명이 포함되어 커밋/PR 제목 및 본문의 압축성이 떨어지고 API 응답 지연(Latency)이 늘어납니다.

* **작업별 권장 설정 범위**:
  * **Commit (`git-ai commit`)**: `300 ~ 500`
    * 제목(72자 이내)과 1~2개 핵심 불릿 본문으로 압축된 결과를 유도하기에 충분하며 토큰 낭비를 방지합니다.
  * **PR (`git-ai pr`)**: `800 ~ 1200`
    * 개요, 변경 상세 불릿(3개 이상), 체크리스트 등 마크다운 구조가 온전히 완성될 수 있도록 여유 공간을 확보해 절단 위험을 방지합니다. |

### 2. 실험 및 재현성 가이드라인

* **결과 재현성을 위한 추천 설정**:
  * 동일한 코드 변경점에 대해 일관된 커밋 메시지를 생성하려면 `--temperature 0.0` 또는 `0.1`로 설정하여 확률적 무작위성을 최소화하세요.
* **대규모 PR 초안 작성 실험**:
  * 변경 파일 수가 많고 상세한 개요 및 마크다운 불릿 목록이 필요한 경우 토큰 제한으로 인한 본문 잘림을 방지하기 위해 `--max-tokens 800` 이상으로 확장하여 실행하세요.

  ---

##  AI 출력 보정 전략: 재생성(Redo) vs 규칙 기반 후처리(Post-processing)

본 도구는 API 호출 제약과 CLI 특성을 고려해 **"API 1회 호출 + 로컬 규칙 기반 후처리"** 구조를 채택했습니다. 재생성(Redo)과 후처리(Post-processing) 전략의 기술적 트레이드오프와 상황별 가이드라인은 다음과 같습니다.

### 1. 트레이드오프 비교 분석

| 비교 항목 | 재생성 (Redo / Multi-turn Re-prompting) | 규칙 기반 후처리 (Rule-based Post-processing) [채택] |
| :--- | :--- | :--- |
| **정확도 (Accuracy)** | LLM이 이전 지적 사항을 반영해 문맥을 재해석하므로 자연스러운 어조 수정 및 문맥 요약 품질이 우수함 | 문자열 슬라이싱, 정규식 치환 등 확정적 규칙에 의존하므로 문맥적 재작성이나 새로운 의미 추론은 불가능함 |
| **제어성 (Controllability)** | 재생성 결과 역시 확률적(Probabilistic)이므로 재시도 시에도 글자 수 초과나 포맷 위반이 다시 발생할 위험이 있음 | 파이썬 로직을 통해 공백 트림(`.strip()`), 글자 수 초과 감지, 민감정보 마스킹 등을 **100% 확정적(Deterministic)**으로 제어 |
| **비용 및 지연 (Cost & Latency)** | 추가 호출마다 API 토큰 비용이 배수로 증가하며, 네트워크 RTT가 추가되어 CLI 응답 지연이 심화됨 | **추가 API 비용 0원**, 로컬 메모리 상에서 수 밀리초(ms) 이내에 즉시 처리되어 빠른 터미널 인터랙션 보장 |
| **인프라 안정성** | 상위 엔드포인트의 일시적 트래픽 스파이크(503) 및 Rate Limit(429) 위험 노출 빈도가 호출 횟수에 비례해 증가 | 호출 횟수를 단 1회로 고정하여 외부 의존성 및 API 장애 노출을 최소화 |

### 2. 전략 채택 이유 및 상황별 가이드라인

* **현재 아키텍처 채택 이유**
  * 터미널 CLI 환경은 **빠른 응답 속도(Low Latency)**와 **비용 효율성**이 최우선입니다.
  * 따라서 사소한 포맷 이슈로 매번 API를 다시 호출하기보다는, 1차 생성 후 로컬 파이썬 로직(`display_output`, `apply_safe_mode`)으로 검증·경고를 제공하고 최종 확정은 사용자가 판단하는 Human-in-the-Loop 방식을 적용했습니다.

* **상황별 권장 전략**
  * **후처리(Post-processing) 적용 상황**:
    * 앞뒤 공백 및 개행 제거 (`.strip()`)
    * API Key, 비밀번호 등 민감정보 마스킹 (`re.sub`)
    * 제목 글자 수 초과, 불릿/섹션 누락에 대한 경고 피드백 제공
  * **재생성(Redo) 고려 상황**:
    * diff 분석 결과와 완전히 무관한 심각한 환각(Hallucination)이 발생한 경우
    * 필수 마크다운 섹션(##) 전체가 누락되어 로컬 파싱으로 복구가 불가능한 경우