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

@app.route('/api/members', methods=['GET'])
def get_members():
    """Get all members"""
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

# Error handlers
@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Not Found'}), 404

@app.errorhandler(500)
def server_error(error):
    return jsonify({'error': 'Server Error'}), 500

if __name__ == '__main__':
    app.run(debug=False, host='0.0.0.0', port=8080)
