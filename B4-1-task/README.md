# 🚀 Developer Portfolio (반응형 포트폴리오 웹사이트)

> 바닐라 자바스크립트(Vanilla JS), HTML5, CSS3를 활용하여 제작한 반응형 개인 포트폴리오 웹사이트입니다.  
> 외부 프레임워크/라이브러리 없이 순수 웹 표준 기술만을 사용하여 **"사용자 이벤트 → 상태 변경 → 화면 업데이트"** 단방향 데이터 흐름을 직접 구현했습니다.

---

## 🔗 배포 및 저장소 URL

- **Live Demo (배포 사이트):** [https://yijuseong.github.io/Codyssey/B4-1-task/](https://yijuseong.github.io/Codyssey/B4-1-task/)
- **GitHub Repository:** [https://github.com/yijuseong/Codyssey](https://github.com/yijuseong/Codyssey)

---


## 🛠️ 기술 스택 (Tech Stack)

- **Markup:** HTML5 (시맨틱 마크업)
- **Styling:** CSS3 (Flexbox, CSS Grid, CSS Variables, Media Queries)
- **Script:** JavaScript (ES6+, DOM Manipulation, Fetch API, Async/Await, Intersection Observer)
- **Icons & Fonts:** Font Awesome 6.4, Google Fonts (Inter)
- **Deployment:** GitHub Pages

---

## ✨ 주요 기능 및 특징

### 1. 반응형 웹 디자인 (Responsive Web)
- **Mobile-First** 방식을 적용하여 모바일, 태블릿(768px 이상), 데스크톱(1024px 이상) 전 환경에 최적화된 레이아웃 제공
- Flexbox와 CSS Grid (`auto-fit`, `minmax`)를 조합해 디바이스 크기에 맞춰 카드 수와 크기가 동적으로 변경

### 2. 다크 모드 (Dark Mode)
- CSS 변수(`:root` 및 `[data-theme="dark"]`)를 통한 테마 시스템 구축
- 사용자의 테마 선택 상태를 `localStorage`에 저장하여 새로고침 후에도 설정 유지

### 3. GitHub API 동적 연동 (Projects)
- `fetch` 및 `async/await`를 사용하여 본인의 GitHub public 저장소 목록을 비동기로 로드
- **상태 관리 기반 UI 렌더링:**
  - **로딩 중:** 스피너 애니메이션 표시
  - **성공 시:** `map` 및 템플릿 리터럴로 프로젝트 카드 동적 생성
  - **에러/한도 초과(403) 시:** 에러 메시지 및 [재시도] 버튼 표시
  - **빈 상태 시:** 프로젝트가 없음을 안내하는 메시지 표시

### 4. Contact 폼 유효성 검사 (Form Validation)
- 필수 입력 필드(이름, 이메일, 메시지) 검증
- 정규표현식을 사용한 이메일 형식 검증
- 입력 오류 시 해당 입력창 하단에 실시간 에러 메시지 노출 (`input` 이벤트 동기화)
- 폼 제출 성공 시 기본 동작 방지(`preventDefault`) 후 성공 안내 메시지 표시

---

## 📂 프로젝트 폴더 구조

```text
B4-1-task/
├── index.html          # 메인 HTML (시맨틱 구조)
├── css/
│   └── style.css       # 메인 스타일시트 (CSS 변수, 반응형, 애니메이션)
├── js/
│   └── app.js          # 메인 자바스크립트 (상태 관리, DOM 조작, API 연동)
├── images/             # 프로필 및 스크린샷 이미지
│   └── profile.jpg
└── README.md           # 프로젝트 문서