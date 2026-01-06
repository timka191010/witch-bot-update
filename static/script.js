// Инициализация Telegram WebApp
let tg = window.Telegram.WebApp;
tg.expand();
tg.ready();

// Получаем данные пользователя из Telegram
let userId = tg.initDataUnsafe?.user?.id || 12345;
let userName = tg.initDataUnsafe?.user?.first_name || 'Тестовый пользователь';
let userFullName = `${tg.initDataUnsafe?.user?.first_name || ''} ${tg.initDataUnsafe?.user?.last_name || ''}`.trim();

console.log('👤 Telegram User ID:', userId);
console.log('👤 Telegram User Name:', userName);

// Применяем тему Telegram
if (tg.themeParams) {
    document.documentElement.style.setProperty('--tg-theme-bg-color', tg.themeParams.bg_color);
    document.documentElement.style.setProperty('--tg-theme-text-color', tg.themeParams.text_color);
    document.documentElement.style.setProperty('--tg-theme-hint-color', tg.themeParams.hint_color);
    document.documentElement.style.setProperty('--tg-theme-link-color', tg.themeParams.link_color);
    document.documentElement.style.setProperty('--tg-theme-button-color', tg.themeParams.button_color);
    document.documentElement.style.setProperty('--tg-theme-button-text-color', tg.themeParams.button_text_color);
}

// Переключение вкладок
document.querySelectorAll('.nav-btn:not(.admin-btn)').forEach(tab => {
    tab.addEventListener('click', () => {
        document.querySelectorAll('.page-section').forEach(c => c.classList.remove('active'));
        document.querySelectorAll('.nav-btn:not(.admin-btn)').forEach(t => t.classList.remove('active'));
        tab.classList.add('active');
        const tabName = tab.dataset.tab || tab.getAttribute('onclick').match(/'([^']+)'/)[1];
        document.getElementById(tabName).classList.add('active');
        
        // Загрузка участников для вкладки members
        if (tabName === 'members') {
            loadMembers();
        }
        
        tg.HapticFeedback.impactOccurred('light');
    });
});

// === УЧАСТНИКИ (ИСПРАВЛЕННАЯ ФУНКЦИЯ) ===
async function loadMembers() {
  try {
    console.log('🔄 Загрузка участниц...');
    const response = await fetch('/api/members.json');  // ← .json!
    
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    
    const data = await response.json();
    const members = Object.values(data);  // объект → массив
    
    console.log('✅ Получено:', members.length, 'ведьм');
    
    const container = document.getElementById('membersList');  // ← ТВОЙ ID!
    
    if (!container) {
      console.error('❌ #membersList не найден');
      return;
    }
    
    // Красивый список по твоему CSS
    container.innerHTML = members.map(m => `
      <div class="member-card">
        <div class="member-emoji">${m.emoji || '👤'}</div>
        <div>
          <div class="member-name">${m.name}</div>
          <div class="member-role">${m.title}</div>
          <small style="color:#9ca3ff;">${m.joinedAt || 'Не указано'}</small>
        </div>
      </div>
    `).join('');
    
    console.log('🎉 Участницы отрисованы!');
  } catch (error) {
    console.error('❌ Ошибка участников:', error);
    document.getElementById('membersList').innerHTML = 
      '<p style="text-align:center; color:#fecaca;">Ошибка загрузки списка 😿</p>';
  }
}

// Отправка формы (твой старый код)
const form = document.getElementById('surveyForm');
if (form) {
    form.addEventListener('submit', async (e) => {
        e.preventDefault();
        tg.HapticFeedback.impactOccurred('medium');
        
        const formData = {
            name: document.querySelector('input[name="name"]').value,
            birthDate: document.querySelector('input[name="birthDate"]').value,
            telegramUsername: document.querySelector('input[name="telegramUsername"]').value,
            familyStatus: document.querySelector('select[name="familyStatus"]').value,
            children: document.querySelector('input[name="children"]').value,
            interests: document.querySelector('textarea[name="interests"]').value,
            topics: document.querySelector('textarea[name="topics"]').value,
            goals: document.querySelector('textarea[name="goals"]').value,
            source: document.querySelector('input[name="source"]').value,
            useTelegram: document.querySelector('input[name="useTelegram"]').checked
        };
        
        try {
            const response = await fetch('/api/survey', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify(formData)
            });
            
            if (response.ok) {
                tg.showAlert('✅ Анкета отправлена!');
                form.reset();
            } else {
                tg.showAlert('❌ Ошибка отправки');
            }
        } catch (error) {
            tg.showAlert('❌ Ошибка сети');
        }
    });
}

// Загрузка статуса пользователя (твой старый код)
async function loadUserStatus() {
    try {
        const response = await fetch(`/api/user_status/${userId}`);
        const data = await response.json();
        
        const statusElement = document.querySelector('.status-pending');
        const userNameElement = document.getElementById('userName');
        
        if (data.exists) {
            userNameElement.textContent = data.name;
            if (data.status === 'approved') {
                statusElement.textContent = '✅ Одобрена';
                statusElement.style.color = '#00FF00';
            } else if (data.status === 'rejected') {
                statusElement.textContent = '❌ Отклонена';
                statusElement.style.color = '#FF4444';
            } else {
                statusElement.textContent = '⏳ Ожидает';
                statusElement.style.color = '#FFA500';
            }
        }
    } catch (error) {
        console.error('Статус:', error);
    }
}

// Инициализация
document.addEventListener('DOMContentLoaded', () => {
  console.log('🚀 Witch Club готов!');
  loadUserStatus();
});
