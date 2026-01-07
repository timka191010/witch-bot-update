import os
from flask import Flask, render_template, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

app = Flask(__name__, template_folder='templates', static_folder='static')
app.secret_key = os.environ.get('SECRET_KEY', 'witch-secret-2026')

# Database
database_url = os.environ.get('DATABASE_URL')
if database_url and database_url.startswith('postgres://'):
    database_url = database_url.replace('postgres://', 'postgresql://', 1)

app.config['SQLALCHEMY_DATABASE_URI'] = database_url or 'sqlite:///witch_club.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

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

# Routes
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
            agreement=data.get('agreement', False)
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

if __name__ == '__main__':
    app.run(debug=False)
