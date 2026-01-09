
Full Flask App


# Full app.py for Witch Club

import os
import json
from datetime import datetime
from flask import Flask, render_template, request, jsonify, session, redirect
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from dotenv import load_dotenv
import psycopg2

load_dotenv()

app = Flask(__name__, template_folder='templates')
CORS(app)

# ==================== CONFIG ====================
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///witch_club.db')

# Если это PostgreSQL от Render, преобразуем URL
if DATABASE_URL and DATABASE_URL.startswith('postgresql://'):
    DATABASE_URL = DATABASE_URL.replace('postgresql://', 'postgresql+psycopg2://', 1)

app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URL
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# ==================== MODELS ====================
class Member(db.Model):
    __tablename__ = 'members'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), unique=True, nullable=False)
    emoji = db.Column(db.String(10), nullable=False)
    title = db.Column(db.String(255), nullable=False)
    birth_date = db.Column(db.Date, nullable=True)
    about = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'emoji': self.emoji,
            'title': self.title,
            'birth_date': self.birth_date.strftime('%d.%m.%Y') if self.birth_date else None,
            'bio': self.about
        }

class Survey(db.Model):
    __tablename__ = 'surveys'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    birth_date = db.Column(db.Date, nullable=True)
    telegram = db.Column(db.String(255), nullable=False)
    marital_status = db.Column(db.String(100), nullable=True)
    children = db.Column(db.Text, nullable=True)
    hobbies = db.Column(db.Text, nullable=True)
    topics = db.Column(db.Text, nullable=True)
    goal = db.Column(db.Text, nullable=True)
    source = db.Column(db.String(255), nullable=True)
    about = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    approved = db.Column(db.Boolean, default=False)
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'birth_date': self.birth_date.strftime('%d.%m.%Y') if self.birth_date else None,
            'telegram': self.telegram,
            'marital_status': self.marital_status,
            'children': self.children,
            'hobbies': self.hobbies,
            'topics': self.topics,
            'goal': self.goal,
            'source': self.source,
            'about': self.about,
            'created_at': self.created_at.strftime('%d.%m.%Y %H:%M'),
            'approved': self.approved
        }

# ==================== ROUTES ====================

@app.route('/')
@app.route('/setup/add-members')
def index():
    """Главная страница с участницами и формой анкеты"""
    return render_template('index.html')

@app.route('/api/members', methods=['GET'])
def get_members():
    """Получить список одобренных участниц"""
    members = Member.query.all()
    return jsonify({
        'status': 'success',
        'members': [m.to_dict() for m in members]
    })

@app.route('/api/survey', methods=['POST'])
def add_survey():
    """Добавить новую анкету"""
    try:
        data = request.get_json()
        
        # Преобразуем дату
        birth_date = None
        if data.get('birth_date'):
            try:
                birth_date = datetime.strptime(data['birth_date'], '%Y-%m-%d').date()
            except:
                birth_date = None
        
        survey = Survey(
            name=data.get('name', '').strip(),
            birth_date=birth_date,
            telegram=data.get('telegram', '').strip().replace('@', ''),
            marital_status=data.get('marital_status', ''),
            children=data.get('children', ''),
            hobbies=data.get('hobbies', ''),
            topics=data.get('topics', ''),
            goal=data.get('goal', ''),
            source=data.get('source', ''),
            about=data.get('about', '')
        )
        
        db.session.add(survey)
        db.session.commit()
        
        return jsonify({
            'status': 'success',
            'message': 'Анкета успешно отправлена!',
            'survey_id': survey.id
        }), 201
    
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'status': 'error',
            'error': str(e)
        }), 400

@app.route('/api/surveys', methods=['GET'])
def get_surveys():
    """Получить все анкеты (только для админа)"""
    if not session.get('admin_logged_in'):
        return jsonify({'status': 'error', 'error': 'Unauthorized'}), 401
    
    surveys = Survey.query.order_by(Survey.created_at.desc()).all()
    return jsonify({
        'status': 'success',
        'surveys': [s.to_dict() for s in surveys]
    })

@app.route('/api/surveys/<int:survey_id>/approve', methods=['POST'])
def approve_survey(survey_id):
    """Одобрить анкету и добавить участницу"""
    if not session.get('admin_logged_in'):
        return jsonify({'status': 'error', 'error': 'Unauthorized'}), 401
    
    try:
        survey = Survey.query.get(survey_id)
        if not survey:
            return jsonify({'status': 'error', 'error': 'Survey not found'}), 404
        
        # Создаем новую участницу
        member = Member(
            name=survey.name,
            emoji='✨',  # По умолчанию
            title='Ведьма',  # По умолчанию
            birth_date=survey.birth_date,
            about=survey.about
        )
        
        survey.approved = True
        db.session.add(member)
        db.session.commit()
        
        return jsonify({
            'status': 'success',
            'message': f'{survey.name} одобрена и добавлена!'
        })
    
    except Exception as e:
        db.session.rollback()
        return jsonify({'status': 'error', 'error': str(e)}), 400

@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    """Вход админа"""
    if request.method == 'POST':
        password = request.form.get('password', '')
        admin_password = os.getenv('ADMIN_PASSWORD', 'admin123')
        
        if password == admin_password:
            session['admin_logged_in'] = True
            return redirect('/admin/dashboard')
        else:
            return render_template('admin_login.html', error='Неверный пароль'), 401
    
    return render_template('admin_login.html')

@app.route('/admin/dashboard')
def admin_dashboard():
    """Админ панель"""
    if not session.get('admin_logged_in'):
        return redirect('/admin/login')
    
    return render_template('admin_dashboard.html')

@app.route('/admin/logout')
def admin_logout():
    """Выход админа"""
    session.clear()
    return redirect('/')

@app.route('/migrate')
def migrate():
    """Миграция из JSON"""
    try:
        # Читаем members.json
        with open('api/members.json', 'r', encoding='utf-8') as f:
            members_data = json.load(f)
        
        count = 0
        for member in members_data:
            # Преобразуем дату
            birth_date = None
            if member.get('birthDate'):
                try:
                    birth_date = datetime.strptime(member['birthDate'], '%d.%m.%Y').date()
                except:
                    pass
            
            # Проверяем, есть ли уже такая участница
            existing = Member.query.filter_by(name=member['name']).first()
            if not existing:
                m = Member(
                    name=member['name'],
                    emoji=member.get('emoji', '✨'),
                    title=member.get('title', 'Ведьма'),
                    birth_date=birth_date,
                    about=member.get('about', '')
                )
                db.session.add(m)
                count += 1
        
        db.session.commit()
        
        return jsonify({
            'status': 'success',
            'message': f'Добавлено {count} участниц из JSON'
        })
    
    except Exception as e:
        db.session.rollback()
        return jsonify({'status': 'error', 'error': str(e)}), 400

# ==================== ERROR HANDLERS ====================

@app.errorhandler(404)
def not_found(error):
    return jsonify({'status': 'error', 'error': 'Not found'}), 404

@app.errorhandler(500)
def server_error(error):
    return jsonify({'status': 'error', 'error': 'Server error'}), 500

# ==================== INITIALIZATION ====================

@app.before_request
def create_tables():
    """Создать таблицы, если их нет"""
    db.create_all()

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        print("✅ Таблицы созданы!")
    
    port = int(os.getenv('PORT', 8080))
    app.run(debug=os.getenv('FLASK_ENV') == 'development', port=port)
