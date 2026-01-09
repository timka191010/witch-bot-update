from flask import Flask, jsonify, request, render_template_string, redirect
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from datetime import datetime
import os
import random
import requests
from sqlalchemy import func

app = Flask(__name__, template_folder='templates')

# ==================== CONFIG ====================

# Абсолютный путь для БД
DB_PATH = os.path.join(os.path.dirname(__file__), 'witch_club.db')
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{DB_PATH}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['JSON_AS_ASCII'] = False

db = SQLAlchemy(app)
CORS(app)

print(f"📊 БД путь: {DB_PATH}")

# ==================== TELEGRAM ====================

BOT_TOKEN = '8500508012:AAEMuWXEsZsUfiDiOV50xFw928Tn7VUJRH8'
CHAT_LINK = 'https://t.me/+S32BT0FT6w0xYTBi'
ADMIN_PASSWORD = 'witches2026'

# ==================== MODELS ====================

class Survey(db.Model):
    __tablename__ = 'surveys'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    telegram = db.Column(db.String(255), nullable=False, unique=True)
    birth_date = db.Column(db.String(50), nullable=True)
    about = db.Column(db.Text, nullable=True)
    approved = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'telegram': self.telegram,
            'birth_date': self.birth_date,
            'about': self.about,
            'approved': self.approved,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }


class Member(db.Model):
    __tablename__ = 'members'
    
    id = db.Column(db.Integer, primary_key=True)
    survey_id = db.Column(db.Integer, db.ForeignKey('surveys.id'), nullable=False)
    name = db.Column(db.String(255), nullable=False)
    title = db.Column(db.String(255), nullable=True)
    emoji = db.Column(db.String(10), default='🧙‍♀️')
    bio = db.Column(db.Text, default='')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'survey_id': self.survey_id,
            'name': self.name,
            'title': self.title,
            'emoji': self.emoji,
            'bio': self.bio,
            'created_at': self.created_at.isoformat()
        }


TITLES = [
    '⭐ ведьма звёзд',
    '🌙 ведьма луны',
    '☀️ ведьма солнца',
    '🔥 ведьма огня',
    '💧 ведьма воды',
    '🌪️ ведьма ветра',
    '🪨 ведьма земли',
    '🌲 ведьма лесов',
    '⛰️ ведьма гор',
    '🌊 ведьма морей',
    '💭 ведьма грёз',
    '🧵 ведьма судеб',
    '⏳ ведьма времени',
    '🌑 ведьма теней',
    '💡 ведьма света',
    '🕷️ ведьма тьмы',
    '🧪 ведьма зелья',
    '📿 ведьма заклятий',
    '✨ ведьма чар',
    '🎭 ведьма иллюзий',
    '🪞 ведьма реальности',
    '😴 ведьма снов',
    '👹 ведьма кошмаров',
    '💕 ведьма любви',
    '🔪 ведьма ненависти',
    '😄 ведьма радости',
    '😢 ведьма печали',
    '😠 ведьма гнева',
    '🧘 ведьма спокойствия',
    '⚔️ ведьма войны',
    '☮️ ведьма мира',
    '💀 ведьма смерти',
    '🌱 ведьма жизни',
    '🎂 ведьма рождения',
    '🔄 ведьма возрождения',
    '🌪️ ведьма гибели',
    '🛡️ ведьма спасения',
    '🚫 ведьма проклятий',
    '✋ ведьма благословений',
    '🎲 ведьма кармы',
    '🦋 ведьма превращений',
    '🪶 ведьма полёта',
    '👁️ ведьма невидимости',
    '🏥 ведьма исцеления',
    '☠️ ведьма яда',
    '🌀 ведьма зарубежных миров',
]


def send_telegram_message(username, message_text):
    """Отправить сообщение через бот"""
    try:
        payload = {
            'chat_id': username,
            'text': message_text,
            'parse_mode': 'HTML',
            'disable_web_page_preview': True
        }
        
        response = requests.post(
            f'https://api.telegram.org/bot{BOT_TOKEN}/sendMessage',
            json=payload,
            timeout=10
        )
        
        if response.ok:
            print(f"✅ Telegram: {username}")
            return True
        else:
            print(f"❌ Telegram: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Ошибка: {str(e)}")
        return False


# ==================== PATH SETUP ====================

def get_template_path(filename):
    """Получить правильный путь к файлу шаблона"""
    path1 = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'templates', filename))
    if os.path.exists(path1):
        return path1
    
    path2 = os.path.abspath(os.path.join(os.path.dirname(__file__), 'templates', filename))
    if os.path.exists(path2):
        return path2
    
    path3 = f'/opt/render/project/src/templates/{filename}'
    if os.path.exists(path3):
        return path3
    
    return path1


# ==================== API - AUTH ====================

@app.route('/api/login', methods=['POST'])
def api_login():
    """Проверка пароля админки"""
    try:
        data = request.get_json()
        password = data.get('password', '')
        
        if password == ADMIN_PASSWORD:
            return jsonify({'status': 'success', 'redirect': '/dashboard'}), 200
        else:
            return jsonify({'error': 'Неверный пароль'}), 401
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ==================== STATIC ROUTES ====================

@app.route('/')
def index():
    """Главная страница с формой анкеты"""
    try:
        template_path = get_template_path('index.html')
        with open(template_path, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        print(f"Error loading index: {e}")
        return jsonify({'error': f'Index not found: {str(e)}'}), 404


@app.route('/admin')
def admin_login():
    """Страница входа в админку"""
    try:
        template_path = get_template_path('admin_login.html')
        with open(template_path, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        print(f"Error loading login: {e}")
        return jsonify({'error': f'Login page not found: {str(e)}'}), 404


@app.route('/admin/login')
def admin_login_redirect():
    """Редирект для совместимости"""
    return redirect('/admin')


@app.route('/dashboard')
def dashboard():
    """Админ панель с анкетами"""
    try:
        template_path = get_template_path('admin_dashboard.html')
        with open(template_path, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        print(f"Error loading dashboard: {e}")
        return jsonify({'error': f'Dashboard not found: {str(e)}'}), 404


@app.route('/stats')
def stats_page():
    """Страница со статистикой"""
    try:
        template_path = get_template_path('admin_stats.html')
        with open(template_path, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        print(f"Error loading stats: {e}")
        return jsonify({'error': f'Stats page not found: {str(e)}'}), 404


@app.route('/witches')
def witches_page():
    """Публичная страница со всеми ведьмами"""
    try:
        template_path = get_template_path('witches.html')
        with open(template_path, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        print(f"Error loading witches page: {e}")
        return jsonify({'error': f'Witches page not found: {str(e)}'}), 404


# ==================== API - SURVEYS ====================

@app.route('/api/surveys', methods=['POST'])
def create_survey():
    """Создать анкету - потом редирект на /dashboard"""
    try:
        data = request.get_json()
        
        if not data.get('name') or not data.get('telegram'):
            return jsonify({'error': 'Заполните имя и Telegram'}), 400
        
        existing = Survey.query.filter_by(telegram=data['telegram'].replace('@', '')).first()
        if existing:
            return jsonify({'error': 'Анкета с этим Telegram уже существует'}), 400
        
        survey = Survey(
            name=data['name'],
            telegram=data['telegram'].replace('@', ''),
            birth_date=data.get('birth_date', ''),
            about=data.get('about', '')
        )
        
        db.session.add(survey)
        db.session.commit()
        
        return jsonify({'status': 'success', 'survey': survey.to_dict(), 'redirect': '/dashboard'}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@app.route('/api/surveys', methods=['GET'])
def get_surveys():
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        
        surveys = Survey.query.filter_by(approved=False).order_by(
            Survey.created_at.desc()
        ).paginate(page=page, per_page=per_page)
        
        return jsonify({
            'status': 'success',
            'surveys': [s.to_dict() for s in surveys.items],
            'total': surveys.total,
            'pages': surveys.pages,
            'current_page': page
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/surveys/<int:survey_id>', methods=['GET'])
def get_survey(survey_id):
    try:
        survey = Survey.query.get(survey_id)
        if not survey:
            return jsonify({'error': 'Анкета не найдена'}), 404
        
        return jsonify({'status': 'success', 'survey': survey.to_dict()}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/surveys/<int:survey_id>/approve', methods=['POST'])
def approve_survey(survey_id):
    """✅ ОДОБРИТЬ И ОТПРАВИТЬ СООБЩЕНИЕ"""
    try:
        survey = Survey.query.get(survey_id)
        if not survey:
            return jsonify({'error': 'Анкета не найдена'}), 404
        
        survey.approved = True
        db.session.commit()
        
        member = Member(
            survey_id=survey.id,
            name=survey.name,
            title=random.choice(TITLES),
            emoji='🧙‍♀️',
            bio=''
        )
        db.session.add(member)
        db.session.commit()
        
        # 📱 ОТПРАВЛЯЕМ В TELEGRAM
        username = survey.telegram.replace('@', '').strip()
        message = f"""🎉 <b>Поздравляем, {survey.name}!</b>

Ваша анкета одобрена! 🧙‍♀️✨

🔗 <a href="{CHAT_LINK}">Присоединиться к клубу</a>

Ждём вас! 💜"""
        
        send_telegram_message(username, message)
        
        return jsonify({'status': 'success', 'message': 'Участница добавлена', 'member': member.to_dict()}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@app.route('/api/surveys/<int:survey_id>/reject', methods=['POST'])
def reject_survey(survey_id):
    try:
        survey = Survey.query.get(survey_id)
        if not survey:
            return jsonify({'error': 'Анкета не найдена'}), 404
        
        db.session.delete(survey)
        db.session.commit()
        
        return jsonify({'status': 'success'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


# ==================== API - MEMBERS ====================

@app.route('/api/members', methods=['GET'])
def get_members():
    try:
        members = Member.query.order_by(Member.created_at.desc()).all()
        print(f"📊 Всего членов: {len(members)}")
        for m in members:
            print(f"  - {m.name}: {m.title}")
        
        return jsonify({'status': 'success', 'members': [m.to_dict() for m in members]}), 200
    except Exception as e:
        print(f"❌ Ошибка в get_members: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/members/<int:member_id>', methods=['GET'])
def get_member(member_id):
    try:
        member = Member.query.get(member_id)
        if not member:
            return jsonify({'error': 'Участница не найдена'}), 404
        
        return jsonify({'status': 'success', 'member': member.to_dict()}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/members/<int:member_id>/update', methods=['POST'])
def update_member(member_id):
    """Изменить титул участницы"""
    try:
        member = Member.query.get(member_id)
        if not member:
            return jsonify({'error': 'Участница не найдена'}), 404
        
        data = request.get_json()
        
        if 'title' in data:
            member.title = data['title']
        if 'bio' in data:
            member.bio = data['bio']
        if 'emoji' in data:
            member.emoji = data['emoji']
        if 'name' in data:
            member.name = data['name']
        
        db.session.commit()
        
        return jsonify({'status': 'success', 'member': member.to_dict()}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@app.route('/api/members/<int:member_id>', methods=['DELETE'])
def delete_member(member_id):
    try:
        member = Member.query.get(member_id)
        if not member:
            return jsonify({'error': 'Участница не найдена'}), 404
        
        survey_id = member.survey_id
        db.session.delete(member)
        
        survey = Survey.query.get(survey_id)
        if survey:
            db.session.delete(survey)
        
        db.session.commit()
        
        return jsonify({'status': 'success'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


# ==================== API - ADMIN ====================

@app.route('/api/admin/stats', methods=['GET'])
def admin_stats():
    try:
        total_surveys = Survey.query.count()
        approved = Survey.query.filter_by(approved=True).count()
        pending = total_surveys - approved
        members = Member.query.count()
        
        return jsonify({
            'status': 'success',
            'stats': {
                'total_surveys': total_surveys,
                'approved_surveys': approved,
                'pending_surveys': pending,
                'total_members': members
            }
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/admin/surveys/pending', methods=['GET'])
def admin_pending_surveys():
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        
        surveys = Survey.query.filter_by(approved=False).order_by(
            Survey.created_at.desc()
        ).paginate(page=page, per_page=per_page)
        
        return jsonify({
            'status': 'success',
            'surveys': [s.to_dict() for s in surveys.items],
            'total': surveys.total,
            'pages': surveys.pages,
            'current_page': page
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/admin/members', methods=['GET'])
def admin_all_members():
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 50, type=int)
        
        members = Member.query.order_by(
            Member.created_at.desc()
        ).paginate(page=page, per_page=per_page)
        
        return jsonify({
            'status': 'success',
            'members': [m.to_dict() for m in members.items],
            'total': members.total,
            'pages': members.pages,
            'current_page': page
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/admin/titles', methods=['GET'])
def admin_titles():
    """Получить все доступные титулы для выбора"""
    try:
        return jsonify({'status': 'success', 'titles': TITLES}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ==================== API - INIT DB ====================

@app.route('/api/init-db', methods=['POST', 'GET'])
def init_db_endpoint():
    """Инициализировать БД с участницами"""
    try:
        # Удаляем старых
        Member.query.delete()
        Survey.query.delete()
        db.session.commit()
        print("🗑️ Старые данные удалены")
        
        default_members = [
            {'name': 'Мария Зуева', 'title': '🌌 Верховная Ведьма', 'emoji': '🔮'},
            {'name': 'Юлия Пиндюрина', 'title': '⭐ Ведьма Звёздного Пути', 'emoji': '✨'},
            {'name': 'Елена Клыкова', 'title': '🌿 Ведьма Трав и Эликсиров', 'emoji': '🌿'},
            {'name': 'Наталья Гудкова', 'title': '🔥 Ведьма Огненного Круга', 'emoji': '🔥'},
            {'name': 'Екатерина Когай', 'title': '🌙 Ведьма Лунного Света', 'emoji': '🌙'},
            {'name': 'Елена Пустовит', 'title': '💎 Ведьма Кристаллов', 'emoji': '💎'},
            {'name': 'Елена Провосуд', 'title': '⚡ Ведьма Грозовых Ветров', 'emoji': '⚡'},
            {'name': 'Анна Моисеева', 'title': '🦋 Ведьма Превращений', 'emoji': '🦋'},
        ]
        
        for idx, member_data in enumerate(default_members, 1):
            survey = Survey(
                name=member_data['name'],
                telegram=f'witch_{idx}',
                approved=True
            )
            db.session.add(survey)
            db.session.flush()
            
            member = Member(
                survey_id=survey.id,
                name=member_data['name'],
                title=member_data['title'],
                emoji=member_data['emoji'],
                bio=''
            )
            db.session.add(member)
        
        db.session.commit()
        print("✅ БД инициализирована с 8 участницами!")
        
        return jsonify({
            'status': 'success',
            'message': '✅ Инициализировано 8 участниц!'
        }), 200
    except Exception as e:
        db.session.rollback()
        print(f"❌ Ошибка инициализации: {e}")
        return jsonify({'error': str(e)}), 500


# ==================== HEALTH CHECK ====================

@app.route('/api/health', methods=['GET'])
def health():
    return jsonify({'status': 'ok'}), 200


# ==================== INIT ====================

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        print("✅ Таблицы созданы")
        # Инициализируем БД при старте
        try:
            member_count = Member.query.count()
            if member_count == 0:
                print("🔄 БД пуста, инициализирую...")
                Member.query.delete()
                Survey.query.delete()
                db.session.commit()
                
                default_members = [
                    {'name': 'Мария Зуева', 'title': '🌌 Верховная Ведьма', 'emoji': '🔮'},
                    {'name': 'Юлия Пиндюрина', 'title': '⭐ Ведьма Звёздного Пути', 'emoji': '✨'},
                    {'name': 'Елена Клыкова', 'title': '🌿 Ведьма Трав и Эликсиров', 'emoji': '🌿'},
                    {'name': 'Наталья Гудкова', 'title': '🔥 Ведьма Огненного Круга', 'emoji': '🔥'},
                    {'name': 'Екатерина Когай', 'title': '🌙 Ведьма Лунного Света', 'emoji': '🌙'},
                    {'name': 'Елена Пустовит', 'title': '💎 Ведьма Кристаллов', 'emoji': '💎'},
                    {'name': 'Елена Провосуд', 'title': '⚡ Ведьма Грозовых Ветров', 'emoji': '⚡'},
                    {'name': 'Анна Моисеева', 'title': '🦋 Ведьма Превращений', 'emoji': '🦋'},
                ]
                
                for idx, member_data in enumerate(default_members, 1):
                    survey = Survey(
                        name=member_data['name'],
                        telegram=f'witch_{idx}',
                        approved=True
                    )
                    db.session.add(survey)
                    db.session.flush()
                    
                    member = Member(
                        survey_id=survey.id,
                        name=member_data['name'],
                        title=member_data['title'],
                        emoji=member_data['emoji'],
                        bio=''
                    )
                    db.session.add(member)
                
                db.session.commit()
                print("✅ Добавлено 8 участниц!")
            else:
                print(f"✅ БД уже содержит {member_count} членов")
        except Exception as e:
            print(f"❌ Ошибка инициализации: {e}")
    
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)), debug=False)
