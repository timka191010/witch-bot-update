// Инициализация Telegram WebApp
let tg = window.Telegram.WebApp;
tg.expand();
tg.ready();

// Данные пользователя
let userId = tg.initDataUnsafe?.user?.id || 12345;
let userName = tg.initDataUnsafe?.user?.first_name || 'Тестовый пользователь';
console.log('👤 User:', userId, userName);

// Тема Telegram
if (tg.themeParams) {
  Object.entries(tg.themeParams).forEach(([key, value]) => {
    document.documentElement.style.setProperty(`--tg-theme-${key.replace(/([A-Z])/g, '-$1').toLowerCase()}`, value);
  });
}

// Переключение вкладок
document.querySelectorAll('.nav-btn:not(.admin-btn)').forEach(tab => {
  tab.addEventListener('click', (e) => {
    const onclick = tab.getAttribute('onclick');
    const sectionId = onclick ? onclick.match(/'([^']+)'/)[1] : tab.dataset.tab;
    
    document.querySelectorAll('.page-section').forEach(c => c.classList.remove('active'));
    document.querySelectorAll('.nav-btn:not(.admin-btn)').forEach(t => t.classList.remove('active'));
    
    tab.classList.add('active');
    document.getElementById(sectionId).classList.add('active');
    
    if (sectionId === 'members') loadMembers();
    
    tg.HapticFeedback.impactOccurred('light');
  });
});

// === УЧАСТНИЦЫ (ФИНАЛЬНАЯ ВЕРСИЯ) ===
async function loadMembers() {
  document.getElementById('membersList').innerHTML = '🔄 Загрузка...';
  
  fetch('/api/members

    
    if (!response.ok) throw new Error(response.status);
    
    const data = await response.json();
    const members = Object.values(data);
    
    console.log('✅', members.length, 'ведьм');
    
    const container = document.getElementById('membersList');
    if (!container) throw new Error('Нет #membersList');
    
    // Твой CSS‑стиль
    container.innerHTML = members.map(m => `
      <div class="member-card">
        <div class="member-emoji">${m.emoji}</div>
        <div>
          <div class="member-name">${m.name}</div>
          <div class="member-role">${m.title}</div>
          <small style="color:#9ca3ff;">${m.joinedAt || ''}</small>
        </div>
      </div>
    `).join('');
    
  } catch (e) {
    console.error('❌', e);
    document.getElementById('membersList').innerHTML = 
      '<div style="text-align:center;padding:40px;color:#fecaca;">Ошибка загрузки</div>';
  }
}

// Форма анкеты
document.getElementById('surveyForm')?.addEventListener('submit', async (e) => {
  e.preventDefault();
  tg.HapticFeedback.impactOccurred('medium');
  
  const formData = Object.fromEntries(new FormData(e.target));
  
  try {
    const res = await fetch('/api/survey', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify(formData)
    });
    
    if (res.ok) {
      tg.showAlert('✅ Отправлено!');
      e.target.reset();
    } else {
      tg.showAlert('❌ Ошибка');
    }
  } catch {
    tg.showAlert('❌ Сеть');
  }
});

// Статус пользователя
async function loadUserStatus() {
  try {
    const res = await fetch(`/api/user_status/${userId}`);
    const data = await res.json();
    
    const status = document.querySelector('.status-pending');
    const nameEl = document.getElementById('userName');
    
    if (data.exists) {
      nameEl.textContent = data.name;
      status.textContent = data.status === 'approved' ? '✅ Одобрена' : 
                          data.status === 'rejected' ? '❌ Отклонена' : '⏳ Ожидает';
      status.style.color = data.status === 'approved' ? '#00ff00' : 
                          data.status === 'rejected' ? '#ff4444' : '#ffa500';
    }
  } catch(e) {
    console.error('Статус:', e);
  }
}

// Инициализация
document.addEventListener('DOMContentLoaded', () => {
  console.log('🚀 Witch Club готов!');
  loadUserStatus();
});
