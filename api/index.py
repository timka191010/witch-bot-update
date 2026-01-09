from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from datetime import datetime
import os
import random
import requests
from sqlalchemy import func

app = Flask(__name__)

# ==================== CONFIG ====================

app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get(
    'DATABASE_URL',
    'postgresql://user:password@localhost/witch_club'
)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['JSON_AS_ASCII'] = False

db = SQLAlchemy(app)
CORS(app)

# ==================== TELEGRAM ====================

BOT_TOKEN = '8500508012:AAEMuWXEsZsUfiDiOV50xFw928Tn7VUJRH8'
CHAT_LINK = 'https://t.me/+S32BT0FT6w0xYTBi'

# ==================== MODELS ====================

class Survey(db.Model):
    __tablename__ = 'surveys'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    telegram = db.Column(db.String(255), nullable=False)
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


# ==================== DATA ====================

TITLES = [
    '✨ Ведьма года',
    '🔮 Видящая судьбу',
    '🌙 Дочь луны',
    '⚡ Повелительница молний',
    '🌿 Травница',
    '💜 Хранительница магии',
    '🕷️ Плетущая сети',
    '🧿 Защитница',
]


# ==================== TELEGRAM HELPER ====================

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
            print(f"✅ Telegram: сообщение отправлено {username}")
            return True
        else:
            print(f"❌ Telegram error: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Ошибка Telegram: {str(e)}")
        return False


# ==================== API ====================

@app.route('/api/surveys', methods=['POST'])
def create_survey():
    """Создать анкету"""
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
        
        return jsonify({
            'status': 'success',
            'survey': survey.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@app.route('/api/surveys', methods=['GET'])
def get_surveys():
    """Получить неодобренные анкеты"""
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
    """Получить одну анкету"""
    try:
        survey = Survey.query.get(survey_id)
        if not survey:
            return jsonify({'error': 'Анкета не найдена'}), 404
        
        return jsonify({
            'status': 'success',
            'survey': survey.to_dict()
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/surveys/<int:survey_id>/approve', methods=['POST'])
def approve_survey(survey_id):
    """✅ ОДОБРИТЬ АНКЕТУ И ОТПРАВИТЬ СООБЩЕНИЕ"""
    try:
        survey = Survey.query.get(survey_id)
        if not survey:
            return jsonify({'error': 'Анкета не найдена'}), 404
        
        # Отмечаем как одобренную
        survey.approved = True
        db.session.commit()
        
        # Добавляем в членов
        member = Member(
            survey_id=survey.id,
            name=survey.name,
            title=random.choice(TITLES),
            emoji='🧙‍♀️',
            bio=''
        )
        db.session.add(member)
        db.session.commit()
        
        # 📱 ОТПРАВЛЯЕМ СООБЩЕНИЕ В TELEGRAM
        username = survey.telegram.replace('@', '').strip()
        message = f"""🎉 <b>Поздравляем, {survey.name}!</b>

Ваша анкета одобрена! 🧙‍♀️✨

<b>Присоединиться к закрытому клубу:</b>

🔗 <a href="{CHAT_LINK}">Вход в клуб</a>

Ждём вас! 💜"""
        
        send_telegram_message(username, message)
        
        return jsonify({'status': 'success', 'message': 'Участница добавлена'}), 200
    
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@app.route('/api/surveys/<int:survey_id>/reject', methods=['POST'])
def reject_survey(survey_id):
    """Отклонить анкету"""
    try:
        survey = Survey.query.get(survey_id)
        if not survey:
            return jsonify({'error': 'Анкета не найдена'}), 404
        
        db.session.delete(survey)
        db.session.commit()
        
        return jsonify({'status': 'success', 'message': 'Анкета отклонена'}), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@app.route('/api/members', methods=['GET'])
def get_members():
    """Получить всех членов"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        
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


@app.route('/api/stats', methods=['GET'])
def get_stats():
    """Статистика"""
    try:
        total_surveys = db.session.query(func.count(Survey.id)).scalar()
        approved_surveys = db.session.query(func.count(Survey.id)).filter(
            Survey.approved == True
        ).scalar()
        total_members = db.session.query(func.count(Member.id)).scalar()
        
        return jsonify({
            'status': 'success',
            'stats': {
                'total_surveys': total_surveys,
                'approved_surveys': approved_surveys,
                'pending_surveys': total_surveys - approved_surveys,
                'total_members': total_members
            }
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check"""
    return jsonify({'status': 'ok'}), 200


# ==================== INIT ====================

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    
    app.run(
        host='0.0.0.0',
        port=int(os.environ.get('PORT', 5000)),
        debug=os.environ.get('FLASK_ENV') == 'development'
    )

