import os
import requests
import random
from flask import Flask, jsonify, request, render_template, send_from_directory
from flask_cors import CORS
from dotenv import load_dotenv
from supabase import create_client, Client
import uuid
from datetime import datetime

load_dotenv()

# Инициализация
app = Flask(__name__, template_folder='templates', static_folder='templates')
CORS(app)

# Переменные окружения
SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_KEY = os.getenv('SUPABASE_KEY')
BOT_TOKEN = os.getenv('BOT_TOKEN', '8500508012:AAEMuWXEsZsUfiDiOV50xFw928Tn7VUJRH8')
ADMIN_PASSWORD = os.getenv('ADMIN_PASSWORD', 'admin123')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID', '-5015136189')

# Supabase
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

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
print(f"✅ SUPABASE_URL: {SUPABASE_URL}")
print(f"✅ TELEGRAM_CHAT_ID: {TELEGRAM_CHAT_ID}")
print(f"✅ Доступно титулов: {len(TITLES)}")

# ==================== ФУНКЦИИ ====================

def get_random_title():
    """Получить случайный титул"""
    return random.choice(TITLES)

def send_telegram_message(username, message_text):
    """Отправить сообщение в групповой чат"""
    try:
        payload = {
            'chat_id': TELEGRAM_CHAT_ID,  # Групповой чат
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
        print(f"📊 Telegram body: {response.text}")
        
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
        
        response = supabase.table('surveys').insert({
            'id': survey_id,
            'name': data.get('name'),
            'birth_date': data.get('birth_date'),
            'telegram': data.get('telegram'),
            'about': data.get('about'),
            'status': 'pending',
            'created_at': datetime.now().isoformat()
        }).execute()
        
        print(f"✅ Анкета создана: {survey_id}")
        
        return jsonify({'status': 'success', 'id': survey_id}), 201
    except Exception as e:
        print(f"❌ Ошибка создания анкеты: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/surveys/<survey_id>/approve', methods=['POST'])
def approve_survey(survey_id):
    """Одобрить анкету и добавить в участницы"""
    try:
        # Получить данные анкеты
        survey = supabase.table('surveys').select('*').eq('id', survey_id).execute()
        
        if not survey.data:
            return jsonify({'error': 'Survey not found'}), 404
        
        survey_data = survey.data[0]
        
        # Создать участницу с рандомным титулом
        member_id = str(uuid.uuid4())
        random_title = get_random_title()
        
        supabase.table('members').insert({
            'id': member_id,
            'name': survey_data['name'],
            'title': random_title,
            'emoji': '✨',
            'bio': '',
            'created_at': datetime.now().isoformat()
        }).execute()
        
        # Обновить статус анкеты
        supabase.table('surveys').update({'status': 'approved'}).eq('id', survey_id).execute()
        
        # Отправить сообщение в Telegram
        message = f"""🎉 <b>Поздравляем!</b>

Ваша анкета одобрена! 🧙‍♀️✨

Ваш титул: <b>{random_title}</b>

🔗 <a href="https://t.me/+S32BT0FT6w0xYTBi">Присоединиться к клубу</a>

Ждём вас! 💜"""
        
        send_telegram_message(survey_data['telegram'], message)
        
        print(f"✅ Анкета одобрена: {survey_id} -> Титул: {random_title}")
        
        return jsonify({'status': 'success', 'title': random_title}), 200
    except Exception as e:
        print(f"❌ Ошибка одобрения: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/surveys/<survey_id>/reject', methods=['POST'])
def reject_survey(survey_id):
    """Отклонить анкету"""
    try:
        supabase.table('surveys').update({'status': 'rejected'}).eq('id', survey_id).execute()
        
        print(f"✅ Анкета отклонена: {survey_id}")
        
        return jsonify({'status': 'success'}), 200
    except Exception as e:
        print(f"❌ Ошибка отклонения: {str(e)}")
        return jsonify({'error': str(e)}), 500

# ==================== API УЧАСТНИЦЫ ====================

@app.route('/api/members', methods=['GET'])
def get_members():
    """Получить всех участниц"""
    try:
        response = supabase.table('members').select('*').order('created_at', desc=True).execute()
        
        print(f"✅ Загружено участниц: {len(response.data)}")
        
        return jsonify({'members': response.data}), 200
    except Exception as e:
        print(f"❌ Ошибка загрузки участниц: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/members/<member_id>', methods=['DELETE'])
def delete_member(member_id):
    """Удалить участницу"""
    try:
        supabase.table('members').delete().eq('id', member_id).execute()
        
        print(f"✅ Участница удалена: {member_id}")
        
        return jsonify({'status': 'success'}), 200
    except Exception as e:
        print(f"❌ Ошибка удаления: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/members/<member_id>/title', methods=['PUT'])
def update_member_title(member_id):
    """Изменить титул участницы"""
    try:
        data = request.json
        title = data.get('title')
        
        if not title:
            return jsonify({'error': 'Title is required'}), 400
        
        supabase.table('members').update({'title': title}).eq('id', member_id).execute()
        
        print(f"✅ Титул обновлен: {member_id} -> {title}")
        
        return jsonify({'status': 'success'}), 200
    except Exception as e:
        print(f"❌ Ошибка обновления титула: {str(e)}")
        return jsonify({'error': str(e)}), 500

# ==================== ADMIN API ====================

@app.route('/api/admin/login', methods=['POST'])
def admin_login_api():
    """Вход в админку"""
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
    """Получить статистику"""
    try:
        surveys = supabase.table('surveys').select('*').execute()
        members = supabase.table('members').select('*').execute()
        
        total_surveys = len(surveys.data)
        pending = len([s for s in surveys.data if s['status'] == 'pending'])
        approved = len([s for s in surveys.data if s['status'] == 'approved'])
        total_members = len(members.data)
        
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
        print(f"❌ Ошибка статистики: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/admin/surveys/pending', methods=['GET'])
def get_pending_surveys():
    """Получить заявки в ожидании"""
    try:
        response = supabase.table('surveys').select('*').eq('status', 'pending').order('created_at', desc=True).execute()
        
        print(f"✅ Заявки в ожидании: {len(response.data)}")
        
        return jsonify({'surveys': response.data}), 200
    except Exception as e:
        print(f"❌ Ошибка загрузки заявок: {str(e)}")
        return jsonify({'error': str(e)}), 500

# ==================== ТЕСТОВАЯ ОТПРАВКА ====================

@app.route('/api/send-telegram-test/<username>', methods=['GET'])
def send_telegram_test(username):
    """Тестовая отправка сообщения в Telegram"""
    try:
        random_title = get_random_title()
        
        message = f"""🎉 <b>Поздравляем!</b>

Ваша анкета одобрена! 🧙‍♀️✨

Ваш титул: <b>{random_title}</b>

🔗 <a href="https://t.me/+S32BT0FT6w0xYTBi">Присоединиться к клубу</a>

Ждём вас! 💜"""
        
        success = send_telegram_message(username, message)
        
        if success:
            return jsonify({'status': 'success', 'message': f'✅ Сообщение отправлено', 'title': random_title}), 200
        else:
            return jsonify({'status': 'error', 'message': 'Ошибка отправки'}), 500
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/health', methods=['GET'])
def health():
    """Health check"""
    return jsonify({'status': 'ok'}), 200

# ==================== ЗАПУСК ====================

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=8080)
