// Инициализация Telegram WebApp
let tg = window.Telegram.WebApp;
tg.expand();
tg.ready();

// Получаем данные пользователя из Telegram
let userId = tg.initDataUnsafe?.user?.id || 12345; // Fallback для тестирования
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
document.querySelectorAll('.tab').forEach(tab => {
    tab.addEventListener('click', () => {
        document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
        document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
        tab.classList.add('active');
        const tabName = tab.dataset.tab;
        document.getElementById(tabName).classList.add('active');
        
        // Вибрация при переключении вкладок
        tg.HapticFeedback.impactOccurred('light');
    });
});

// Отправка формы
const form = document.getElementById('applicationForm');
if (form) {
    form.addEventListener('submit', async (e) => {
        e.preventDefault();
        console.log('🔥 Форма отправляется!');
        
        // Вибрация при отправке
        tg.HapticFeedback.impactOccurred('medium');
        
        const formData = new FormData(e.target);
        const data = {
            user_id: userId,
            name: formData.get('name'),
            age: formData.get('age'),
            family_status: formData.get('family_status'),
            children: formData.get('children'),
            hobbies: formData.get('hobbies'),
            themes: formData.get('themes'),
            goal: formData.get('goal'),
            source: formData.get('source')
        };
        
        console.log('📤 Отправляем данные:', data);
        
        try {
            const response = await fetch('/api/submit_application', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(data)
            });
            
            const result = await response.json();
            console.log('📥 Получен ответ:', result);
            
            if (result.success) {
                // Успешная вибрация
                tg.HapticFeedback.notificationOccurred('success');
                tg.showAlert('✅ Анкета отправлена! Ожидайте одобрения.');
                e.target.reset();
                // Обновляем статус после отправки
                loadUserStatus();
            } else {
                tg.HapticFeedback.notificationOccurred('error');
                tg.showAlert('❌ Ошибка: ' + result.message);
            }
        } catch (error) {
            tg.HapticFeedback.notificationOccurred('error');
            tg.showAlert('❌ Ошибка отправки: ' + error.message);
            console.error('❌ Ошибка:', error);
        }
    });
}

// Загрузка статуса пользователя
async function loadUserStatus() {
    try {
        const response = await fetch(`/api/user_status/${userId}`);
        const data = await response.json();
        
        console.log('📊 Статус пользователя:', data);
        
        const statusElement = document.querySelector('.status-pending');
        const userNameElement = document.getElementById('userName');
        const userIdElement = document.getElementById('userId');
        
        // Обновляем ID пользователя
        if (userIdElement) {
            userIdElement.textContent = userId;
        }
        
        if (data.exists) {
            // Обновляем имя
            userNameElement.textContent = data.name;
            
            // Обновляем статус
            if (data.status === 'approved') {
                statusElement.textContent = '✅ Одобрена';
                statusElement.className = 'status-approved';
                statusElement.style.color = '#00FF00';
                statusElement.style.background = 'rgba(0, 255, 0, 0.2)';
                statusElement.style.border = '1px solid #00FF00';
                statusElement.style.padding = '5px 10px';
                statusElement.style.borderRadius = '15px';
                statusElement.style.display = 'inline-block';
            } else if (data.status === 'rejected') {
                statusElement.textContent = '❌ Отклонена';
                statusElement.className = 'status-rejected';
                statusElement.style.color = '#FF4444';
                statusElement.style.background = 'rgba(255, 68, 68, 0.2)';
                statusElement.style.border = '1px solid #FF4444';
                statusElement.style.padding = '5px 10px';
                statusElement.style.borderRadius = '15px';
                statusElement.style.display = 'inline-block';
            } else {
                statusElement.textContent = '⏳ Ожидает проверки';
                statusElement.className = 'status-pending';
                statusElement.style.color = '#FFA500';
                statusElement.style.background = 'rgba(255, 165, 0, 0.2)';
                statusElement.style.border = '1px solid #FFA500';
                statusElement.style.padding = '5px 10px';
                statusElement.style.borderRadius = '15px';
                statusElement.style.display = 'inline-block';
            }
        } else {
            userNameElement.textContent = userFullName || 'Не заполнено';
            statusElement.textContent = '📝 Анкета не заполнена';
            statusElement.style.color = 'rgba(255, 255, 255, 0.6)';
        }
    } catch (error) {
        console.error('❌ Ошибка загрузки статуса:', error);
        document.getElementById('userName').textContent = userFullName || 'Ошибка загрузки';
        document.querySelector('.status-pending').textContent = 'Ошибка загрузки';
    }
}

// Загружаем статус при загрузке страницы
window.addEventListener('DOMContentLoaded', () => {
    console.log('✅ Script.js загружен успешно!');
    loadUserStatus();
});
