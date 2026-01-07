import os
from flask import Flask, render_template, request, jsonify, session, redirect, url_for, send_file
from flask_sqlalchemy import SQLAlchemy
from werkzeug.utils import secure_filename
from datetime import datetime
import io
import json

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
    email = db.Column(db.String(150), nullable=False)
    age = db.Column(db.Integer)
    hobbies = db.Column(db.Text)
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
    members = Member.query.all()
    return render_template('index.html', members=members)

@app.route('/survey', methods=['GET', 'POST'])
def survey():
    if request.method == 'POST':
        data = request.get_json()
        
        survey = Survey(
            name=data.get('name'),
            email=data.get('email'),
            age=data.get('age'),
            hobbies=data.get('hobbies')
        )
        db.session.add(survey)
        db.session.commit()
        
        return jsonify({'status': 'success', 'id': survey.id})
    
    return render_template('survey.html')

@app.route('/api/members', methods=['GET'])
def get_members():
    members = Member.query.all()
    return jsonify([{
        'id': m.id,
        'name': m.name,
        'title': m.title,
        'emoji': m.emoji,
        'bio': m.bio
    } for m in members])

@app.route('/api/upcoming-birthdays', methods=['GET'])
def upcoming_birthdays():
    """Получить ближайшие дни рождения (на следующие 30 дней)"""
    from datetime import timedelta
    
    members = Member.query.all()
    today = datetime.now()
    upcoming = []
    
    for member in members:
        if not member.birth_date:
            continue
        
        try:
            # Парсим дату в формате DD.MM.YYYY
            birth_parts = member.birth_date.split('.')
            if len(birth_parts) == 3:
                day, month, year = int(birth_parts[0]), int(birth_parts[1]), int(birth_parts[2])
                
                # Ближайший день рождения в этом году
                next_birthday = datetime(today.year, month, day)
                if next_birthday < today:
                    next_birthday = datetime(today.year + 1, month, day)
                
                days_until = (next_birthday - today).days
                
                if 0 <= days_until <= 30:
                    upcoming.append({
                        'name': member.name,
                        'emoji': member.emoji,
                        'title': member.title,
                        'birth_date': member.birth_date,
                        'days_until': days_until
                    })
        except:
            pass
    
    # Сортируем по дате
    upcoming.sort(key=lambda x: x['days_until'])
    return jsonify(upcoming)

@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        password = request.form.get('password')
        admin_password = os.environ.get('ADMIN_PASSWORD', 'witch2026')
        
        if password == admin_password:
            session['admin'] = True
            return redirect(url_for('admin_dashboard'))
        else:
            return render_template('admin_login.html', error='Неправильный пароль')
    
    return render_template('admin_login.html')

@app.route('/admin/logout')
def admin_logout():
    session.clear()
    return redirect(url_for('admin_login'))

@app.route('/admin')
def admin_dashboard():
    if not session.get('admin'):
        return redirect(url_for('admin_login'))
    
    total_surveys = Survey.query.count()
    approved_surveys = Survey.query.filter_by(approved=True).count()
    pending_surveys = Survey.query.filter_by(approved=False).count()
    total_members = Member.query.count()
    
    pending_list = Survey.query.filter_by(approved=False).all()
    members_list = Member.query.all()
    
    # Получить ближайшие дни рождения
    from datetime import timedelta
    today = datetime.now()
    upcoming_bd = []
    
    for member in members_list:
        if not member.birth_date:
            continue
        
        try:
            birth_parts = member.birth_date.split('.')
            if len(birth_parts) == 3:
                day, month, year = int(birth_parts[0]), int(birth_parts[1]), int(birth_parts[2])
                next_birthday = datetime(today.year, month, day)
                if next_birthday < today:
                    next_birthday = datetime(today.year + 1, month, day)
                
                days_until = (next_birthday - today).days
                
                if 0 <= days_until <= 30:
                    upcoming_bd.append({
                        'name': member.name,
                        'emoji': member.emoji,
                        'birth_date': member.birth_date,
                        'days_until': days_until
                    })
        except:
            pass
    
    upcoming_bd.sort(key=lambda x: x['days_until'])
    
    return render_template('admin_dashboard.html',
        total_surveys=total_surveys,
        approved_surveys=approved_surveys,
        pending_surveys=pending_surveys,
        total_members=total_members,
        pending_list=pending_list,
        members_list=members_list,
        upcoming_bd=upcoming_bd
    )

@app.route('/api/approve/<int:survey_id>', methods=['POST'])
def approve_survey(survey_id):
    if not session.get('admin'):
        return redirect(url_for('admin_login'))
    
    survey = Survey.query.get(survey_id)
    if survey:
        survey.approved = True
        
        # Создаём участницу
        member = Member(
            name=survey.name,
            title=survey.hobbies,
            bio=f"Email: {survey.email}, Возраст: {survey.age}"
        )
        db.session.add(member)
        db.session.commit()
        
        return redirect(url_for('admin_dashboard'))
    
    return 'Survey not found', 404

@app.route('/api/reject/<int:survey_id>', methods=['POST'])
def reject_survey(survey_id):
    if not session.get('admin'):
        return redirect(url_for('admin_login'))
    
    survey = Survey.query.get(survey_id)
    if survey:
        db.session.delete(survey)
        db.session.commit()
    
    return redirect(url_for('admin_dashboard'))

@app.route('/api/remove_member/<int:member_id>', methods=['POST'])
def remove_member(member_id):
    if not session.get('admin'):
        return jsonify({'error': 'Unauthorized'}), 401
    
    member = Member.query.get(member_id)
    if member:
        db.session.delete(member)
        db.session.commit()
    
    return redirect(url_for('admin_dashboard'))

@app.route('/api/update_member/<int:member_id>', methods=['POST'])
def update_member(member_id):
    if not session.get('admin'):
        return jsonify({'error': 'Unauthorized'}), 401
    
    try:
        data = request.get_json()
        member = Member.query.get(member_id)
        
        if not member:
            return jsonify({'error': 'Member not found'}), 404
        
        if 'title' in data:
            member.title = data['title']
        if 'emoji' in data:
            member.emoji = data['emoji']
        if 'birth_date' in data:
            member.birth_date = data['birth_date']
        if 'name' in data:
            member.name = data['name']
        
        db.session.commit()
        return jsonify({'status': 'success'})
    
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 400

@app.route('/api/clear_surveys', methods=['POST'])
def clear_surveys():
    if not session.get('admin'):
        return redirect(url_for('admin_login'))
    
    db.session.query(Survey).filter_by(approved=False).delete()
    db.session.commit()
    
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/load-members', methods=['POST'])
def load_members_from_json():
    """Загрузи членов из JSON в БД"""
    if not session.get('admin'):
        return jsonify({'error': 'Unauthorized'}), 401
    
    try:
        json_path = os.path.join(os.path.dirname(__file__), '../public/members.json')
        with open(json_path, 'r', encoding='utf-8') as f:
            members_data = json.load(f)
        
        count = 0
        for m in members_data:
            # Проверь дубликаты
            existing = Member.query.filter_by(name=m['name']).first()
            if not existing:
                member = Member(
                    name=m['name'],
                    title=m.get('title', ''),
                    emoji=m.get('emoji', '🧙‍♀️'),
                    bio=m.get('bio', ''),
                    birth_date=m.get('birthDate', '')
                )
                db.session.add(member)
                count += 1
        
        db.session.commit()
        return jsonify({'status': 'success', 'loaded': count})
    
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)})

@app.route('/api/export', methods=['GET'])
def export_members():
    if not session.get('admin'):
        return jsonify({'error': 'Unauthorized'}), 401
    
    members = Member.query.all()
    csv = "Name,Title,Emoji,BirthDate\n"
    for m in members:
        csv += f"{m.name},{m.title},{m.emoji},{m.birth_date}\n"
    
    return send_file(
        io.BytesIO(csv.encode()),
        mimetype='text/csv',
        as_attachment=True,
        download_name='members.csv'
    )

@app.route('/health')
def health():
    return jsonify({'status': 'ok'})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port, debug=False)
