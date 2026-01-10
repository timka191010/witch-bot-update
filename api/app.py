import os
import json
from datetime import datetime
from flask import Flask, render_template, request, jsonify, session, redirect
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__, template_folder='templates')
CORS(app)

app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret-key')
DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///witch_club.db')

if DATABASE_URL and DATABASE_URL.startswith('postgresql://'):
    DATABASE_URL = DATABASE_URL.replace('postgresql://', 'postgresql+psycopg2://', 1)

app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URL
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

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
            'approved': self.approved
        }

@app.route('/')
@app.route('/setup/add-members')
def index():
    return render_template('index.html')

@app.route('/api/members', methods=['GET'])
def get_members():
    members = Member.query.all()
    return jsonify({'status': 'success', 'members': [m.to_dict() for m in members]})

@app.route('/api/survey', methods=['POST'])
def add_survey():
    try:
        data = request.get_json()
        birth_date = None
        if data.get('birth_date'):
            try:
                birth_date = datetime.strptime(data['birth_date'], '%Y-%m-%d').date()
            except:
                pass
        
        survey = Survey(
            name=data.get('name', '').strip(),
            birth_date=birth_date,
            telegram=data.get('telegram', '').strip().replace('@', ''),
            about=data.get('about', '')
        )
        db.session.add(survey)
        db.session.commit()
        return jsonify({'status': 'success', 'message': 'OK'}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'status': 'error', 'error': str(e)}), 400

@app.route('/api/surveys', methods=['GET'])
def get_surveys():
    if not session.get('admin_logged_in'):
        return jsonify({'status': 'error'}), 401
    surveys = Survey.query.all()
    return jsonify({'status': 'success', 'surveys': [s.to_dict() for s in surveys]})

@app.route('/api/admin/surveys/pending', methods=['GET'])
def get_pending_surveys():
    if not session.get('admin_logged_in'):
        return jsonify({'status': 'error'}), 401
    surveys = Survey.query.filter_by(approved=False).all()
    return jsonify({
        'status': 'success', 
        'surveys': [
            {
                'id': s.id,
                'name': s.name,
                'telegram': s.telegram,
                'birth_date': s.birth_date.strftime('%d.%m.%Y') if s.birth_date else None,
                'approved': s.approved,
                'created_at': s.created_at.strftime('%d.%m.%Y %H:%M') if s.created_at else None,
                'about': s.about
            } 
            for s in surveys
        ]
    })

@app.route('/api/admin/stats', methods=['GET'])
def get_admin_stats():
    if not session.get('admin_logged_in'):
        return jsonify({'status': 'error'}), 401
    total_surveys = Survey.query.count()
    approved_surveys = Survey.query.filter_by(approved=True).count()
    pending_surveys = Survey.query.filter_by(approved=False).count()
    total_members = Member.query.count()
    
    return jsonify({
        'status': 'success',
        'stats': {
            'total_surveys': total_surveys,
            'approved_surveys': approved_surveys,
            'pending_surveys': pending_surveys,
            'total_members': total_members
        }
    })

@app.route('/api/admin/surveys/<int:survey_id>/approve', methods=['POST'])
def approve_survey(survey_id):
    if not session.get('admin_logged_in'):
        return jsonify({'status': 'error'}), 401
    
    survey = Survey.query.get(survey_id)
    if not survey:
        return jsonify({'status': 'error', 'message': 'Survey not found'}), 404
    
    try:
        # Создаем Member из Survey
        member = Member(
            name=survey.name,
            emoji='✨',
            title='Участница',
            birth_date=survey.birth_date,
            about=survey.about
        )
        survey.approved = True
        
        db.session.add(member)
        db.session.commit()
        return jsonify({'status': 'success', 'message': 'Survey approved'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'status': 'error', 'error': str(e)}), 400

@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        password = request.form.get('password', '')
        if password == os.getenv('ADMIN_PASSWORD', 'admin123'):
            session['admin_logged_in'] = True
            return redirect('/admin/dashboard')
        return render_template('admin_login.html', error='Неверный пароль'), 401
    return render_template('admin_login.html')

@app.route('/admin/dashboard')
def admin_dashboard():
    if not session.get('admin_logged_in'):
        return redirect('/admin/login')
    return render_template('admin_dashboard.html')

@app.route('/migrate')
def migrate():
    try:
        with open('members.json', 'r', encoding='utf-8') as f:
            members_data = json.load(f)
        
        count = 0
        for member in members_data:
            birth_date = None
            if member.get('birthDate'):
                try:
                    birth_date = datetime.strptime(member['birthDate'], '%d.%m.%Y').date()
                except:
                    pass
            
            if not Member.query.filter_by(name=member['name']).first():
                m = Member(
                    name=member['name'],
                    emoji=member.get('emoji', '✨'),
                    title=member.get('title', 'Ведьма'),
                    birth_date=birth_date
                )
                db.session.add(m)
                count += 1
        
        db.session.commit()
        return jsonify({'status': 'success', 'message': f'Добавлено {count} участниц'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'status': 'error', 'error': str(e)}), 400

@app.before_request
def create_tables():
    db.create_all()

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    port = int(os.getenv('PORT', 8080))
    app.run(debug=False, port=port)
