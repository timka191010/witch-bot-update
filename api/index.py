import os
from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import requests
from functools import wraps

app = Flask(__name__, template_folder='templates', static_folder='static')
app.secret_key = os.environ.get('SECRET_KEY', 'witch-secret-2026')

# Database
database_url = os.environ.get('DATABASE_URL')
if database_url and database_url.startswith('postgres://'):
    database_url = database_url.replace('postgres://', 'postgresql://', 1)

app.config['SQLALCHEMY_DATABASE_URI'] = database_url or 'sqlite:///witch_club.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Telegram config
TELEGRAM_BOT_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN')
TELEGRAM_CHAT_ID = os.environ.get('TELEGRAM_CHAT_ID')
CHAT_LINK = os.environ.get('CHAT_LINK', 'https://t.me/witchclub')

# Admin credentials
ADMIN_USERNAME = os.environ.get('ADMIN_USERNAME', 'admin')
ADMIN_PASSWORD = os.environ.get('ADMIN_PASSWORD', 'password')

# Models
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
    name = db.Column(db.String(150), nullable=False)
    title = db.Column(db.String(200))
    emoji = db.Column(db.String(10), default='🧙‍♀️')
    bio = db.Column(db.Text)
    birth_date = db.Column(db.String(20))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

# Create tables
with app.app_context():
    db.create_all()

# Helper functions
def send_telegram_message(telegram_username, user_name):
    """Отправить ссылку на чат в Telegram"""
    if not TELEGRAM_BOT_TOKEN:
        print("⚠️ TELEGRAM_BOT_TOKEN не установлен!")
        return False
    
    try:
        message = f"""
🎉 **ДОБРО ПОЖАЛОВАТЬ В КЛУБ!** 🎉

✨ {user_name}, ваша анкета одобрена!

📝 Ваш Telegram: @{telegram_username}

Присоединяйтесь к нам в чате:
{CHAT_LINK}

С любовью,
Клуб ведьм "Ведьмы не стареют" 🧙‍♀️
        """
        
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        data = {
            "chat_id": f"@{telegram_username}",
            "text": message,
            "parse_mode": "Markdown"
        }
        
        response = requests.post(url, data=data, timeout=5)
        return response.status_code == 200
    except Exception as e:
        print(f"❌ Ошибка отправки Telegram: {str(e)}")
        return False

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'admin_logged_in' not in session:
            return redirect(url_for('admin_login'))
        return f(*args, **kwargs)
    return decorated_function

# Public Routes
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/members', methods=['GET'])
def get_members():
    try:
        members = Member.query.all()
        return jsonify([{
            'id': m.id,
            'name': m.name,
            'title': m.title,
            'emoji': m.emoji,
            'bio': m.bio
        } for m in members])
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/submit-survey', methods=['POST'])
def submit_survey():
    try:
        data = request.json
        
        survey = Survey(
            name=data.get('name', ''),
            birth_date=data.get('birthDate', ''),
            telegram=data.get('telegram', ''),
            marital_status=data.get('maritalStatus', ''),
            children=data.get('children', ''),
            hobbies=data.get('hobbies', ''),
            topics=data.get('topics', ''),
            goal=data.get('goal', ''),
            source=data.get('source', ''),
            agreement=data.get('agreement', False),
            approved=False
        )
        
        db.session.add(survey)
        db.session.commit()
        
        return jsonify({
            'status': 'success',
            'message': 'Анкета успешно отправлена! Ожидайте одобрения.'
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'status': 'error',
            'message': f'Ошибка: {str(e)}'
        }), 400

# Admin Routes
@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
            session['admin_logged_in'] = True
            return redirect(url_for('admin_dashboard'))
        else:
            return render_template('admin_login.html', error='Неверные учетные данные'), 401
    
    return render_template('admin_login.html')

@app.route('/admin/logout')
def admin_logout():
    session.pop('admin_logged_in', None)
    return redirect(url_for('admin_login'))

@app.route('/admin/dashboard')
@login_required
def admin_dashboard():
    surveys = Survey.query.order_by(Survey.created_at.desc()).all()
    stats = {
        'total': len(surveys),
        'approved': len([s for s in surveys if s.approved]),
        'pending': len([s for s in surveys if not s.approved])
    }
    return render_template('admin_dashboard.html', surveys=surveys, stats=stats)

@app.route('/api/admin/approve/<int:survey_id>', methods=['POST'])
@login_required
def approve_survey(survey_id):
    try:
        survey = Survey.query.get(survey_id)
        if not survey:
            return jsonify({'error': 'Анкета не найдена'}), 404
        
        survey.approved = True
        db.session.commit()
        
        # Создать участницу
        member = Member(
            name=survey.name,
            title=f"Ведьма {survey.hobbies.split()[0] if survey.hobbies else ''}",
            emoji='🧙‍♀️',
            bio=survey.hobbies[:100],
            birth_date=survey.birth_date
        )
        db.session.add(member)
        db.session.commit()
        
        # Отправить в Telegram
        send_telegram_message(survey.telegram, survey.name)
        
        return jsonify({
            'status': 'success',
            'message': 'Анкета одобрена! Ссылка отправлена в Telegram.'
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 400

@app.route('/api/admin/reject/<int:survey_id>', methods=['POST'])
@login_required
def reject_survey(survey_id):
    try:
        survey = Survey.query.get(survey_id)
        if not survey:
            return jsonify({'error': 'Анкета не найдена'}), 404
        
        db.session.delete(survey)
        db.session.commit()
        
        return jsonify({
            'status': 'success',
            'message': 'Анкета отклонена.'
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 400

@app.route('/api/admin/stats')
@login_required
def get_stats():
    surveys = Survey.query.all()
    stats = {
        'total': len(surveys),
        'approved': len([s for s in surveys if s.approved]),
        'pending': len([s for s in surveys if not s.approved])
    }
    return jsonify(stats)

if __name__ == '__main__':
    app.run(debug=False)
