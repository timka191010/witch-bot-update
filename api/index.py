import os
from flask import Flask, render_template, request, jsonify, session, redirect, url_for, send_file
from flask_sqlalchemy import SQLAlchemy
from werkzeug.utils import secure_filename
from datetime import datetime
import io

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
    
    return render_template('admin_dashboard.html',
        total_surveys=total_surveys,
        approved_surveys=approved_surveys,
        pending_surveys=pending_surveys,
        total_members=total_members,
        pending_list=pending_list,
        members_list=members_list
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

@app.route('/api/clear_surveys', methods=['POST'])
def clear_surveys():
    if not session.get('admin'):
        return redirect(url_for('admin_login'))
    
    db.session.query(Survey).filter_by(approved=False).delete()
    db.session.commit()
    
    return redirect(url_for('admin_dashboard'))

@app.route('/api/export', methods=['GET'])
def export_members():
    if not session.get('admin'):
        return jsonify({'error': 'Unauthorized'}), 401
    
    members = Member.query.all()
    csv = "Name,Title,Email\n"
    for m in members:
        csv += f"{m.name},{m.title},{m.bio}\n"
    
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
