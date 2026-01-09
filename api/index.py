from flask import Flask, render_template, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

app = Flask(__name__, template_folder='templates', static_folder='static')
app.secret_key = 'witch-secret-2026'

# Database configuration
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///witch_club.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

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
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Member(db.Model):
    __tablename__ = 'members'
    id = db.Column(db.Integer, primary_key=True)
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
    
    # GET - Получить всех участниц
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
    
    # POST - Добавить новую анкету и участницу
    if request.method == 'POST':
        try:
            data = request.get_json()
            
            # Сохраняем в Survey
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
                agreement=data.get('agreement', False)
            )
            db.session.add(survey)
            db.session.commit()
            
            # Добавляем в Members
            member = Member(
                name=data.get('name'),
                title='Новая участница',
                emoji='🧙‍♀️',
                bio=data.get('hobbies', '')[:100]
            )
            db.session.add(member)
            db.session.commit()
            
            return jsonify({'status': 'success', 'message': 'Анкета добавлена'}), 200
        
        except Exception as e:
            db.session.rollback()
            return jsonify({'status': 'error', 'message': str(e)}), 400

# ===== ADMIN ROUTES =====

@app.route('/admin/login')
def admin_login():
    """Admin login page"""
    return render_template('admin_login.html')

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
    """Get all surveys"""
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
                'created_at': s.created_at.isoformat() if s.created_at else None
            })
        return jsonify(surveys_data), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ===== ERROR HANDLERS =====

@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Not Found'}), 404

@app.errorhandler(500)
def server_error(error):
    return jsonify({'error': 'Server Error'}), 500

if __name__ == '__main__':
    app.run(debug=False, host='0.0.0.0', port=8080)
