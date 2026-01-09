import os
import requests
import random
import sqlite3
from flask import Flask, jsonify, request, render_template, send_from_directory
from flask_cors import CORS
from dotenv import load_dotenv
import uuid
from datetime import datetime

load_dotenv()

# Инициализация
app = Flask(__name__, template_folder='templates', static_folder='templates')
CORS(app)

# Переменные окружения
BOT_TOKEN = os.getenv('BOT_TOKEN', '8500508012:AAEMuWXEsZsUfiDiOV50xFw928Tn7VUJRH8')
ADMIN_PASSWORD = os.getenv('ADMIN_PASSWORD', 'witches2026')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID', '-5015136189')

# SQLite БД
DB_PATH = 'witch_club.db'

# Список титулов с эмодзи
TITLES = [
    '🌙 Ведьма луны',
    '⭐ Ведьма звезд',
    '🌃 Ведьма ночи',
    '🌲 Ведьма леса',
    '🌊 Ведьма океана',
    '🔥 Ведьма огня',
    '💧 Ведьма воды',
    '💨 Ведьма ветра',
    '🪨 Ведьма земли',
    '🌿 Ведьма травы',
    '💎 Ведьма камней',
    '✨ Ведьма света',
    '🌑 Ведьма тени',
    '⏳ Ведьма времени',
    '🔮 Ведьма судьбы',
    '🪄 Ведьма магии',
    '💜 Ведьма любви',
    '💫 Ведьма желаний',
    '😴 Ведьма снов',
    '🎯 Ведьма истины',
    '👑 Ведьма красоты',
    '📖 Ведьма мудрости',
    '⚡ Ведьма силы',
    '♾️ Ведьма вечности',
    '🌅 Ведьма рассвета',
    '🌆 Ведьма закатов',
    '🌈 Ведьма радуги',
    '🌹 Ведьма розы',
    '🪷 Ведьма лилии',
    '🛤️ Ведьма пути'
]

print(f"✅ BOT_TOKEN: {BOT_TOKEN[:20]}...")
print(f"✅ DATABASE: {DB_PATH}")
print(f"✅ Доступно титулов: {len(TITLES)}")

# ==================== DATABASE ====================

def init_db():
    """Инициализация БД"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    # Таблица участниц
    c.execute('''CREATE TABLE IF NOT EXISTS members (
        id TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        title TEXT DEFAULT 'Новая участница',
        emoji TEXT DEFAULT '✨',
        bio TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')
    
    # Таблица анкет
    c.execute('''CREATE TABLE IF NOT EXISTS surveys (
        id TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        birth_date TEXT,
        telegram TEXT NOT NULL,
        about TEXT,
        status TEXT DEFAULT 'pending',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')
    
    conn.commit()
    conn.close()
    print("✅ БД инициализирована")

def get_db():
    """Получить подключение к БД"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

init_db()

# ==================== ФУНКЦИИ ====================

def get_random_title():
    """Получить случайный титул"""
    return random.choice(TITLES)

def send_telegram_message(username, message_text):
    """Отправить сообщение в групповой чат"""
    try:
        payload = {
            'chat_id': TELEGRAM_CHAT_ID,
            'text': f"<b>@{username}</b>\n\n{message_text}",
            'parse_mode': 'HTML',
            'disable_web_page_preview': True
        }
        
        response = requests.post(
            f'https://api.telegram.org/bot{BOT_TOKEN}/sendMessage',
            json=payload,
            timeout=10
        )
        
        print(f"📊 Telegram response: {response.status_code}")
        
        if response.ok:
            print(f"✅ Telegram: {username}")
            return True
        else:
            print(f"❌ Telegram error: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Ошибка отправки: {str(e)}")
        return False

# ==================== ГЛАВНАЯ СТРАНИЦА ====================

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/dashboard')
def dashboard():
    return render_template('dashboard.html')

@app.route('/admin/login')
def admin_login():
    return render_template('admin_login.html')

@app.route('/admin/dashboard')
def admin_dashboard():
    return render_template('admin_dashboard.html')

@app.route('/admin/stats')
def admin_stats():
    return render_template('admin_stats.html')

# ==================== API АНКЕТЫ ====================

@app.route('/api/surveys', methods=['POST'])
def create_survey():
    """Создать новую анкету"""
    try:
        data = request.json
        survey_id = str(uuid.uuid4())
        
        conn = get_db()
        c = conn.cursor()
        
        c.execute('''INSERT INTO surveys (id, name, birth_date, telegram, about, status)
                     VALUES (?, ?, ?, ?, ?, 'pending')''',
                  (survey_id, data.get('name'), data.get('birth_date'), 
                   data.get('telegram'), data.get('about')))
        
        conn.commit()
        conn.close()
        
        print(f"✅ Анкета создана: {survey_id}")
        
        return jsonify({'status': 'success', 'id': survey_id}), 201
    except Exception as e:
        print(f"❌ Ошибка: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/surveys/<survey_id>/approve', methods=['POST'])
def approve_survey(survey_id):
    """Одобрить анкету"""
    try:
        conn = get_db()
        c = conn.cursor()
        
        # Получить анкету
        c.execute('SELECT * FROM surveys WHERE id = ?', (survey_id,))
        survey = c.fetchone()
        
        if not survey:
            return jsonify({'error': 'Survey not found'}), 404
        
        # Создать участницу
        member_id = str(uuid.uuid4())
        random_title = get_random_title()
        
        c.execute('''INSERT INTO members (id, name, title, emoji, bio)
                     VALUES (?, ?, ?, '✨', '')''',
                  (member_id, survey['name'], random_title))
        
        # Обновить статус
        c.execute('UPDATE surveys SET status = ? WHERE id = ?', ('approved', survey_id))
        
        conn.commit()
        conn.close()
        
        # Отправить в ТГ
        message = f"""🎉 <b>Поздравляем!</b>

Ваша анкета одобрена! 🧙‍♀️✨

Ваш титул: <b>{random_title}</b>

🔗 <a href="https://t.me/+S32BT0FT6w0xYTBi">Присоединиться к клубу</a>

Ждём вас! 💜"""
        
        send_telegram_message(survey['telegram'], message)
        
        print(f"✅ Анкета одобрена: {survey_id} -> {random_title}")
        
        return jsonify({'status': 'success', 'title': random_title}), 200
    except Exception as e:
        print(f"❌ Ошибка: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/surveys/<survey_id>/reject', methods=['POST'])
def reject_survey(survey_id):
    """Отклонить анкету"""
    try:
        conn = get_db()
        c = conn.cursor()
        
        c.execute('UPDATE surveys SET status = ? WHERE id = ?', ('rejected', survey_id))
        
        conn.commit()
        conn.close()
        
        print(f"✅ Анкета отклонена: {survey_id}")
        
        return jsonify({'status': 'success'}), 200
    except Exception as e:
        print(f"❌ Ошибка: {str(e)}")
        return jsonify({'error': str(e)}), 500

# ==================== API УЧАСТНИЦЫ ====================

@app.route('/api/members', methods=['GET'])
def get_members():
    """Получить участниц"""
    try:
        conn = get_db()
        c = conn.cursor()
        
        c.execute('SELECT * FROM members ORDER BY created_at DESC')
        members = [dict(row) for row in c.fetchall()]
        
        conn.close()
        
        print(f"✅ Загружено: {len(members)}")
        
        return jsonify({'members': members}), 200
    except Exception as e:
        print(f"❌ Ошибка: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/members/<member_id>', methods=['DELETE'])
def delete_member(member_id):
    """Удалить участницу"""
    try:
        conn = get_db()
        c = conn.cursor()
        
        c.execute('DELETE FROM members WHERE id = ?', (member_id,))
        
        conn.commit()
        conn.close()
        
        print(f"✅ Удалена: {member_id}")
        
        return jsonify({'status': 'success'}), 200
    except Exception as e:
        print(f"❌ Ошибка: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/members/<member_id>/title', methods=['PUT'])
def update_member_title(member_id):
    """Изменить титул"""
    try:
        data = request.json
        title = data.get('title')
        
        if not title:
            return jsonify({'error': 'Title required'}), 400
        
        conn = get_db()
        c = conn.cursor()
        
        c.execute('UPDATE members SET title = ? WHERE id = ?', (title, member_id))
        
        conn.commit()
        conn.close()
        
        print(f"✅ Титул обновлен: {member_id}")
        
        return jsonify({'status': 'success'}), 200
    except Exception as e:
        print(f"❌ Ошибка: {str(e)}")
        return jsonify({'error': str(e)}), 500

# ==================== ADMIN API ====================

@app.route('/api/admin/login', methods=['POST'])
def admin_login_api():
    """Вход"""
    try:
        data = request.json
        password = data.get('password')
        
        if password == ADMIN_PASSWORD:
            return jsonify({'status': 'success', 'token': 'admin_token'}), 200
        else:
            return jsonify({'error': 'Invalid password'}), 401
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/admin/stats', methods=['GET'])
def admin_stats_api():
    """Статистика"""
    try:
        conn = get_db()
        c = conn.cursor()
        
        c.execute('SELECT COUNT(*) FROM surveys')
        total_surveys = c.fetchone()[0]
        
        c.execute("SELECT COUNT(*) FROM surveys WHERE status = 'pending'")
        pending = c.fetchone()[0]
        
        c.execute("SELECT COUNT(*) FROM surveys WHERE status = 'approved'")
        approved = c.fetchone()[0]
        
        c.execute('SELECT COUNT(*) FROM members')
        total_members = c.fetchone()[0]
        
        conn.close()
        
        return jsonify({
            'status': 'success',
            'stats': {
                'total_surveys': total_surveys,
                'pending_surveys': pending,
                'approved_surveys': approved,
                'total_members': total_members
            }
        }), 200
    except Exception as e:
        print(f"❌ Ошибка: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/admin/surveys/pending', methods=['GET'])
def get_pending_surveys():
    """Заявки"""
    try:
        conn = get_db()
        c = conn.cursor()
        
        c.execute("SELECT * FROM surveys WHERE status = 'pending' ORDER BY created_at DESC")
        surveys = [dict(row) for row in c.fetchall()]
        
        conn.close()
        
        print(f"✅ Заявок: {len(surveys)}")
        
        return jsonify({'surveys': surveys}), 200
    except Exception as e:
        print(f"❌ Ошибка: {str(e)}")
        return jsonify({'error': str(e)}), 500

# ==================== ТЕСТ ====================

@app.route('/api/send-telegram-test/<username>', methods=['GET'])
def send_telegram_test(username):
    """Тестовая отправка"""
    try:
        random_title = get_random_title()
        
        message = f"""🎉 <b>Поздравляем!</b>

Ваша анкета одобрена! 🧙‍♀️✨

Ваш титул: <b>{random_title}</b>

🔗 <a href="https://t.me/+S32BT0FT6w0xYTBi">Присоединиться к клубу</a>

Ждём вас! 💜"""
        
        success = send_telegram_message(username, message)
        
        if success:
            return jsonify({'status': 'success', 'title': random_title}), 200
        else:
            return jsonify({'status': 'error'}), 500
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/health', methods=['GET'])
def health():
    return jsonify({'status': 'ok'}), 200

# ==================== ЗАПУСК ====================

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=8080)
