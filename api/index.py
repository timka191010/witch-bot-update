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

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///witch_club.db'
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


# ==================== API ====================

@app.route('/api/surveys', methods=['POST'])
def create_survey():
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
        
        return jsonify({'status': 'success', 'survey': survey.to_dict()}), 201
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


@app.route('/api/members', methods=['GET'])
def get_members():
    try:
        members = Member.query.order_by(Member.created_at.desc()).all()
        return jsonify({'status': 'success', 'members': [m.to_dict() for m in members]}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/members/<int:member_id>/update', methods=['POST'])
def update_member(member_id):
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
        
        db.session.commit()
        
        return jsonify({'status': 'success', 'member': member.to_dict()}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@app.route('/api/stats', methods=['GET'])
def get_stats():
    try:
        total_surveys = Survey.query.count()
        approved = Survey.query.filter_by(approved=True).count()
        members = Member.query.count()
        
        return jsonify({
            'status': 'success',
            'stats': {
                'total_surveys': total_surveys,
                'approved_surveys': approved,
                'pending': total_surveys - approved,
                'members': members
            }
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/health', methods=['GET'])
def health():
    return jsonify({'status': 'ok'}), 200


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    
    app.run(host='0.0.0.0', port=8080, debug=True)
