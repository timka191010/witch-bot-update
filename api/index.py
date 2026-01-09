import random
from flask import Flask, render_template, request, jsonify, redirect
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

app = Flask(__name__, template_folder='templates', static_folder='static')
app.secret_key = 'witch-secret-2026'

# Database configuration
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///witch_club.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Рандомные титулы для новых участниц
TITLES = [
    'Ведьма знаний 📚',
    'Королева магии ✨',
    'Хранительница секретов 🔮',
    'Мастер зелий 🧪',
    'Древняя мудрость 👑',
    'Волшебница луны 🌙',
    'Дива чар 💫',
    'Повелительница стихий 🔥',
    'Звёздная ведьма ⭐',
    'Королевна тьмы 🖤'
]

# 8 основных ведьм
DEFAULT_MEMBERS = [
    {'name': 'Мария Зуева', 'title': '👑 Верховная Ведьма', 'emoji': '🔮', 'bio': ''},
    {'name': 'Елена Клыкова', 'title': '🌿 Ведьма Трав и Эликсиров', 'emoji': '🌿', 'bio': ''},
    {'name': 'Елена Пустовит', 'title': '💎 Ведьма Кристаллов', 'emoji': '💎', 'bio': ''},
    {'name': 'Елена Провосуд', 'title': '⚡ Ведьма Грозовых Ветров', 'emoji': '⚡', 'bio': ''},
    {'name': 'Юлия Пиндюрина', 'title': '⭐ Ведьма Звёздного Пути', 'emoji': '⭐', 'bio': ''},
    {'name': 'Наталья Гудкова', 'title': '🔥 Ведьма Огненного Круга', 'emoji': '🔥', 'bio': ''},
    {'name': 'Екатерина Когай', 'title': '🌙 Ведьма Лунного Света', 'emoji': '🌙', 'bio': ''},
    {'name': 'Анна Моисеева', 'title': '✨ Ведьма Магии', 'emoji': '✨', 'bio': ''},
]

# ===== DATABASE MODELS =====
class Survey(db.Model):
    __tablename__ = 'surveys'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    birth_date = db.Column(db.String(20))
    telegram = db.Column(db.String(150), nullable=False)
    marital_status = db.Column(db.String(50))
    children = db.Column(db.Text)
    hobbies = db.Column(db.Text)
    topics = db.Column(db.Text)
    goal = db.Column(db.Text)
    source = db.Column(db.String(150))
    agreement = db.Column(db.Boolean, default=False)
    approved = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Member(db.Model):
    __tablename__ = 'members'
    id = db.Column(db.Integer, primary_key=True)
    survey_id = db.Column(db.Integer)
    name = db.Column(db.String(150), nullable=False)
    title = db.Column(db.String(200))
    emoji = db.Column(db.String(10), default='🧙‍♀️')
    bio = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

# Create database tables
with app.app_context():
    db.create_all()

# ===== ROUTES =====

@app.route('/')
def index():
    """Main page"""
    return render_template('index.html')

@app.route('/api/members', methods=['GET', 'POST', 'OPTIONS'])
def handle_members():
    """Get all members or add new member"""
    
    # CORS preflight
    if request.method == 'OPTIONS':
        return '', 200
    
    # GET - Получить ТОЛЬКО ОДОБРЕННЫХ участниц
    if request.method == 'GET':
        try:
            members = Member.query.all()
            members_data = []
            for m in members:
                members_data.append({
                    'id': m.id,
                    'name': m.name,
                    'title': m.title,
                    'emoji': m.emoji,
                    'bio': m.bio
                })
            return jsonify(members_data), 200
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    # POST - Добавить анкету (НЕ добавляем в членов сразу!)
    if request.method == 'POST':
        try:
            data = request.get_json()
            
            # Сохраняем анкету БЕЗ одобрения
            survey = Survey(
                name=data.get('name'),
                birth_date=data.get('birthDate'),
                telegram=data.get('telegram'),
                marital_status=data.get('maritalStatus'),
                children=data.get('children'),
                hobbies=data.get('hobbies'),
                topics=data.get('topics'),
                goal=data.get('goal'),
                source=data.get('source'),
                agreement=data.get('agreement', False),
                approved=False
            )
            db.session.add(survey)
            db.session.commit()
            
            return jsonify({'status': 'success', 'message': 'Анкета отправлена. Ожидайте одобрения'}), 200
        
        except Exception as e:
            db.session.rollback()
            return jsonify({'status': 'error', 'message': str(e)}), 400

# ===== ADMIN ROUTES =====

@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    """Admin login page"""
    if request.method == 'POST':
        data = request.get_json()
        if data.get('password') == 'witch2026':
            return jsonify({'status': 'success'}), 200
        else:
            return jsonify({'status': 'error', 'message': 'Неверный пароль'}), 401
    
    return render_template('admin_login.html')

@app.route('/admin/logout')
def admin_logout():
    """Admin logout"""
    return redirect('/admin/login')

@app.route('/admin/dashboard')
def admin_dashboard():
    """Admin dashboard"""
    return render_template('admin_dashboard.html')

@app.route('/admin/stats')
def admin_stats():
    """Admin stats"""
    return render_template('admin_stats.html')

@app.route('/api/surveys', methods=['GET'])
def get_surveys():
    """Получить ВСЕ анкеты (для админа)"""
    try:
        surveys = Survey.query.all()
        surveys_data = []
        for s in surveys:
            surveys_data.append({
                'id': s.id,
                'name': s.name,
                'telegram': s.telegram,
                'birth_date': s.birth_date,
                'marital_status': s.marital_status,
                'approved': s.approved,
                'created_at': s.created_at.isoformat() if s.created_at else None
            })
        return jsonify(surveys_data), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/surveys/<int:survey_id>/approve', methods=['POST'])
def approve_survey(survey_id):
    """Одобрить анкету и добавить в участницы"""
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
        
        return jsonify({'status': 'success', 'message': 'Анкета удалена'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@app.route('/api/members/<int:member_id>/delete', methods=['POST'])
def delete_member(member_id):
    """Удалить участницу"""
    try:
        member = Member.query.get(member_id)
        if not member:
            return jsonify({'error': 'Участница не найдена'}), 404
        db.session.delete(member)
        db.session.commit()
        return jsonify({'status': 'success'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@app.route('/api/load-default-members', methods=['POST'])
def load_default_members():
    """Загрузить 8 основных ведьм"""
    try:
        count = 0
        for member_data in DEFAULT_MEMBERS:
            # Проверяем, не существует ли уже
            existing = Member.query.filter_by(name=member_data['name']).first()
            if not existing:
                member = Member(
                    name=member_data['name'],
                    title=member_data['title'],
                    emoji=member_data['emoji'],
                    bio=member_data['bio']
                )
                db.session.add(member)
                count += 1
        
        db.session.commit()
        return jsonify({'status': 'success', 'count': count}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'status': 'error', 'message': str(e)}), 500

# ===== ERROR HANDLERS =====

@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Not Found'}), 404

@app.errorhandler(500)
def server_error(error):
    return jsonify({'error': 'Server Error'}), 500

if __name__ == '__main__':
    app.run(debug=False, host='0.0.0.0', port=8080)
