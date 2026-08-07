/**
 * Application State
 */
const state = {
  theme: localStorage.getItem('theme') || 'light',
  isMenuOpen: false,
  selectedLanguage: 'all',
  projects: {
    data: [],
    status: 'IDLE', // IDLE, LOADING, SUCCESS, ERROR, EMPTY
    error: null,
  },
  form: {
    fields: { name: '', email: '', message: '' },
    errors: { name: '', email: '', message: '' },
  },
};

// GitHub API 사용자 ID 설정 (본인 ID로 변경 가능)
const GITHUB_USERNAME = 'YiJuseong';

/* ==========================================================================
   1. DOM Elements Selection
   ========================================================================== */
const elements = {
  html: document.documentElement,
  header: document.getElementById('header'),
  themeToggleBtn: document.getElementById('theme-toggle'),
  hamburgerBtn: document.getElementById('hamburger'),
  navMenu: document.getElementById('nav-menu'),
  navLinks: document.querySelectorAll('.nav-link'),
  scrollTopBtn: document.getElementById('scroll-top'),
  projectsContainer: document.getElementById('projects-container'),
  contactForm: document.getElementById('contact-form'),
  profileImg: document.getElementById('profile-img'),
  languageFilter: document.querySelector('#language-filter'),
  formInputs: {
    name: document.getElementById('name'),
    email: document.getElementById('email'),
    message: document.getElementById('message'),
  },
  formErrors: {
    name: document.getElementById('name-error'),
    email: document.getElementById('email-error'),
    message: document.getElementById('message-error'),
  },
  formSuccess: document.getElementById('form-success'),
};

/* ==========================================================================
   2. Render Functions (State -> UI Update)
   ========================================================================== */
// 다크 모드 테마 렌더링
const renderTheme = () => {
  elements.html.setAttribute('data-theme', state.theme);
  const icon = elements.themeToggleBtn.querySelector('i');
  if (state.theme === 'dark') {
    icon.className = 'fa-solid fa-sun';
  } else {
    icon.className = 'fa-solid fa-moon';
  }
};

// 햄버거 메뉴 렌더링
const renderNavMenu = () => {
  if (state.isMenuOpen) {
    elements.navMenu.classList.add('active');
  } else {
    elements.navMenu.classList.remove('active');
  }
};

// Projects 섹션 API 상태별 렌더링
const renderProjects = () => {
  const { status, data, error } = state.projects;
  const selectedLanguage = state.selectedLanguage || 'all'; // ✨ 선택된 언어 상태 가져오기

  if (status === 'LOADING') {
    elements.projectsContainer.innerHTML = `
      <div class="state-container">
        <div class="spinner"></div>
        <p>GitHub 프로젝트를 불러오는 중입니다...</p>
      </div>
    `;
    return;
  }

  if (status === 'ERROR') {
    elements.projectsContainer.innerHTML = `
      <div class="state-container">
        <p style="color: var(--error-color); margin-bottom: 1rem;">${error}</p>
        <button id="retry-btn" class="btn btn-primary">다시 시도</button>
      </div>
    `;
    document.getElementById('retry-btn').addEventListener('click', fetchGitHubProjects);
    return;
  }

  if (status === 'EMPTY') {
    elements.projectsContainer.innerHTML = `
      <div class="state-container">
        <p>표시할 공개 프로젝트가 없습니다.</p>
      </div>
    `;
    return;
  }

  if (status === 'SUCCESS') {
    // ✨ 1. 선택된 언어 상태에 따라 data 배열 filter() 수행
    const filteredData = data.filter((project) => {
      if (selectedLanguage === 'all') return true;
      return project.language === selectedLanguage;
    });

    // ✨ 2. 필터링 결과 해당 언어의 프로젝트가 0개일 때 예외 처리
    if (filteredData.length === 0) {
      elements.projectsContainer.innerHTML = `
        <div class="state-container">
          <p>해당 언어로 작성된 프로젝트가 없습니다.</p>
        </div>
      `;
      return;
    }

    // ✨ 3. 필터링된 배열(filteredData)로 카드 HTML 생성
    const cardsHTML = filteredData
      .map(({ name, description, html_url, stargazers_count, language }) => `
        <article class="project-card">
          <div>
            <h3 class="project-title">${name}</h3>
            <p class="project-desc">${description || '설명이 없습니다.'}</p>
          </div>
          <div>
            <div class="project-meta">
              <span><i class="fa-solid fa-code"></i> ${language || 'N/A'}</span>
              <span><i class="fa-solid fa-star"></i> ${stargazers_count}</span>
            </div>
            <a href="${html_url}" target="_blank" rel="noopener noreferrer" class="project-link">
              GitHub 바로가기 <i class="fa-solid fa-arrow-up-right-from-square"></i>
            </a>
          </div>
        </article>
      `).join('');

    elements.projectsContainer.innerHTML = `<div class="projects-grid">${cardsHTML}</div>`;
  }
};

// Form 폼 에러/유효성 상태 렌더링
const renderFormValidation = () => {
  Object.keys(state.form.fields).forEach((field) => {
    const inputEl = elements.formInputs[field];
    const errorEl = elements.formErrors[field];
    const errorMessage = state.form.errors[field];

    if (errorMessage) {
      inputEl.classList.add('invalid');
      errorEl.textContent = errorMessage;
    } else {
      inputEl.classList.remove('invalid');
      errorEl.textContent = '';
    }
  });
};

/* ==========================================================================
   3. Actions & Event Handlers
   ========================================================================== */
// 테마 전환 액션
const toggleTheme = () => {
  state.theme = state.theme === 'light' ? 'dark' : 'light';
  localStorage.setItem('theme', state.theme);
  renderTheme();
};

// 햄버거 메뉴 토글
const toggleNavMenu = () => {
  state.isMenuOpen = !state.isMenuOpen;
  renderNavMenu();
};

// GitHub API 비동기 연동
const fetchGitHubProjects = async () => {
  state.projects.status = 'LOADING';
  renderProjects();

  try {
    const response = await fetch(`https://api.github.com/users/${GITHUB_USERNAME}/repos?sort=updated&per_page=6`);
    
    if (response.status === 403) {
      throw new Error('API 요청 한도가 초과되었습니다. 잠시 후 다시 시도해주세요.');
    }
    
    if (!response.ok) {
      throw new Error('프로젝트를 불러올 수 없습니다.');
    }

    const repos = await response.json();

    if (repos.length === 0) {
      state.projects.status = 'EMPTY';
    } else {
      state.projects.data = repos;
      state.projects.status = 'SUCCESS';
    }
  } catch (err) {
    state.projects.status = 'ERROR';
    state.projects.error = err.message;
  } finally {
    renderProjects();
  }
};

// 스크롤 이벤트 처리 (Header 스타일 & Top 버튼)
const handleScroll = () => {
  const scrollY = window.scrollY;

  // 네비게이션 배경색 전환 (기준: 60px)
  if (scrollY > 60) {
    elements.header.classList.add('scrolled');
  } else {
    elements.header.classList.remove('scrolled');
  }

  // 스크롤 탑 버튼 노출 (기준: 300px)
  if (scrollY > 300) {
    elements.scrollTopBtn.classList.add('visible');
  } else {
    elements.scrollTopBtn.classList.remove('visible');
  }
};

// 폼 입력 검증 메서드
const validateForm = () => {
  let isValid = true;
  const { name, email, message } = state.form.fields;
  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

  state.form.errors = { name: '', email: '', message: '' };

  if (!name.trim()) {
    state.form.errors.name = '이름을 입력해주세요.';
    isValid = false;
  }

  if (!email.trim()) {
    state.form.errors.email = '이메일을 입력해주세요.';
    isValid = false;
  } else if (!emailRegex.test(email)) {
    state.form.errors.email = '올바른 이메일 형식이 아닙니다.';
    isValid = false;
  }

  if (!message.trim()) {
    state.form.errors.message = '메시지를 입력해주세요.';
    isValid = false;
  }

  renderFormValidation();
  return isValid;
};

// 폼 제출 핸들러
const handleFormSubmit = (e) => {
  e.preventDefault();

  // 입력값 상태에 동기화
  state.form.fields.name = elements.formInputs.name.value;
  state.form.fields.email = elements.formInputs.email.value;
  state.form.fields.message = elements.formInputs.message.value;

  if (validateForm()) {
    elements.formSuccess.textContent = '메시지가 성공적으로 전송되었습니다!';
    elements.contactForm.reset();
    state.form.fields = { name: '', email: '', message: '' };
    setTimeout(() => {
      elements.formSuccess.textContent = '';
    }, 5000);
  }
};

// Intersection Observer (스크롤 애니메이션)
const setupScrollAnimation = () => {
  const observer = new IntersectionObserver((entries) => {
    entries.forEach((entry) => {
      if (entry.isIntersecting) {
        entry.target.classList.add('show');
      }
    });
  }, { threshold: 0.2 });

  document.querySelectorAll('.animate-on-scroll').forEach((el) => observer.observe(el));
};

// 이미지 로드 실패(error) 처리 
const handleImageError = (e) => {
  e.target.src = 'https://via.placeholder.com/300x300?text=Profile+Image';
};

if (elements.languageFilter) {
  elements.languageFilter.addEventListener('change', (e) => {
    state.selectedLanguage = e.target.value; // 선택된 값으로 상태 업데이트
    renderProjects();                       // 변경된 상태로 화면 다시 렌더링
  });
}

/* ==========================================================================
   4. Event Listeners Initializer
   ========================================================================== */
const initEventListeners = () => {
  elements.themeToggleBtn.addEventListener('click', toggleTheme);
  elements.hamburgerBtn.addEventListener('click', toggleNavMenu);
  
  // 모바일 메뉴 링크 클릭 시 메뉴 닫기
  elements.navLinks.forEach((link) => {
    link.addEventListener('click', () => {
      if (state.isMenuOpen) {
        state.isMenuOpen = false;
        renderNavMenu();
      }
    });
  });

  // 스크롤 탑 버튼
  elements.scrollTopBtn.addEventListener('click', () => {
    window.scrollTo({ top: 0, behavior: 'smooth' });
  });

  // 스크롤 이벤트
  window.addEventListener('scroll', handleScroll);

  // 폼 이벤트
  elements.contactForm.addEventListener('submit', handleFormSubmit);
  Object.keys(elements.formInputs).forEach((key) => {
    elements.formInputs[key].addEventListener('input', (e) => {
      state.form.fields[key] = e.target.value;
      if (state.form.errors[key]) {
        validateForm();
      }
    });
  });
};

// 이미지 로드 실패 이벤트
if (elements.profileImg) {
  // { once: true } 옵션을 주면 대체 이미지마저 로드 실패했을 때 일어나는 무한 루프 에러를 방지할 수 있습니다.
  elements.profileImg.addEventListener('error', handleImageError, { once: true });
}

/* ==========================================================================
   5. App Initialization
   ========================================================================== */
const init = () => {
  renderTheme();
  initEventListeners();
  setupScrollAnimation();
  fetchGitHubProjects();
};

document.addEventListener('DOMContentLoaded', init);