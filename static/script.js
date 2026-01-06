// ====================================
// WITCH CLUB MINIAPP - ПОЛНЫЙ script.js
// ====================================

// Telegram WebApp
const tg = window.Telegram.WebApp;
tg.expand();
tg.ready();

// Пользователь
const userId = tg.initDataUnsafe?.user?.id || 'guest_' + Date.now();
const userName = tg.initDataUnsafe?.user?.first_name || 'Таинственная Ведьма';
console.log('👤 User:', userId, userName);

// Тема
document.documentElement.setAttribute('data-theme', tg.colorScheme === 'dark' ? 'dark' : 'light');
if (tg.themeParams?.bg_color) document.body.style.backgroundColor = tg.themeParams.bg_color;

// === ГЛАВНОЕ МЕНЮ ===
document.addEventListener('DOMContentLoaded', () => {
  loadMembers();
  updateUserInfo();
  setupButtons();
  checkMembership();
});

// === ЧТЕНИЕ ДАННЫХ ===
async function loadMembers() {
  const container = document.getElementById('membersList');
  if (!container) return;
  
  try {
    container.innerHTML = '<div class="loading">🔮 Загружаем клуб...</div>';
    
    const response = await fetch('/members.json');
    const members = await response.json();
    
    container.innerHTML = '';
    Object.values(members).forEach(member => {
      container.innerHTML += `
        <div class="member-card">
          <div class="member-header">
            ${member.emoji} <strong>${member.name}</strong>
            <span class="title">${member.title}</span>
          </div>
          <div class="member-date">🎂 ${member.birthDate || 'Неизвестно'}</div>
          <div class="member-date">📅 ${member.joinedAt}</div>
        </div>
      `;
    });
  } catch (error) {
    container.innerHTML = '<div class="error">❌ Ведьмы спрятались!</div>';
    console.error('Load members error:', error);
  }
}

// === ПРОФИЛЬ ===
function updateUserInfo() {
  const userEl = document.getElementById('userName');
  if (userEl) userEl.textContent = userName;
}

function checkMembership() {
  const joinBtn = document.getElementById('joinBtn');
  if (joinBtn) {
    // Проверяем статус (логика твоя)
    joinBtn.addEventListener('click', () => {
      tg.showAlert('🔮 Добро пожаловать в Клуб!');
      tg.MainButton.setText('Мой профиль').show();
    });
  }
}

// === КНОПКИ ===
function setupButtons() {
  // Главная кнопка Telegram
  tg.MainButton.setText('Вступить в Клуб ✨').show();
  tg.MainButton.onClick(() => {
    tg.showAlert('🧙‍♀️ Ты теперь Ведьма!');
    tg.MainButton.setText('Мой Ковен').show();
  });

  // Навигация
  document.querySelectorAll('[data-page]').forEach(btn => {
    btn.addEventListener('click', (e) => {
      const page = e.target.dataset.page;
      showPage(page);
    });
  });
}

// === НАВИГАЦИЯ ===
function showPage(pageName) {
  document.querySelectorAll('.page').forEach(page => page.classList.add('hidden'));
  document.getElementById(pageName)?.classList.remove('hidden');
  
  if (pageName === 'members') loadMembers();
}

// === АНИМАЦИИ ===
tg.HapticFeedback.impactOccurred('light');

// Экспорт для отладки
window.WitchClub = { loadMembers, userId, userName };
console.log('🧙‍♀️ Witch Club готов!');
