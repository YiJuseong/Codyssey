# Git AI Assistant (Git 변경사항 기반 커밋 & PR 자동 생성 CLI)

Git 저장소의 변경 내역(`git status`, `git diff`)을 분석하여 컨벤션에 맞는 **커밋 메시지**와 구조화된 **Pull Request(PR) 초안**을 자동으로 생성해 주는 AI 개발 보조 CLI 도구입니다.

---

## 📌 주요 기능

- **자동 변경사항 감지**: Staged(`git diff --cached`) 및 Unstaged(`git diff`) 코드 변경점을 자동으로 수집 및 감지합니다.
- **표준 커밋 메시지 생성 (`commit`)**: `타입: 제목` 형식과 2~4줄의 간결한 요약 본문을 작성합니다.
- **구조화된 PR 본문 생성 (`pr`)**: `Why`(배경), `What`(변경 내역), `How to Test`(검증 방법) 섹션으로 정돈된 리뷰용 문서를 생성합니다.
- **유연한 CLI 옵션**: 모델 변경(`--model`), 생성 온도(`--temperature`), 토큰 제한(`--max-tokens`) 등을 터미널 인자로 조정할 수 있습니다.

---

## ⚙️ 사전 요구사항

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

## 💡 팁: 어디서든 실행하기 (Alias 등록)

매번 프로젝트 폴더로 이동하지 않고, PC 내 어떤 Git 프로젝트에서든 바로 사용하려면 단축어를 등록하세요.

```bash
# ~/.zshrc 또는 ~/.bashrc 파일에 추가
alias git-ai="/절대경로/Codyssey/b6-2-task/venv/bin/python /절대경로/Codyssey/b6-2-task/main.py"

# 설정 적용
source ~/.zshrc
```

이제 어떤 Git 작업 폴더에서든 `git-ai commit`, `git-ai pr`로 즉시 실행할 수 있습니다.

---

## ⚠️ 주의사항 및 운영 가이드

1. **보안 및 개인정보 보호 (`.gitignore`)**
   - API 키가 포함된 `.env` 파일이나 로컬 가상환경 폴더(`venv/`)는 절대 원격 저장소에 커밋/푸시하지 마세요.
   - 대용량 파일이나 민감 정보(비밀번호, 토큰 등)가 포함된 변경점은 diff 생성 전 검토해야 합니다.
2. **API 사용량 및 Rate Limit**
   - 무료 티어 API 키 사용 시 분당 요청 수(RPM) 제한에 도달할 수 있으므로 과도한 반복 호출을 피해주세요.
