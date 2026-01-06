from flask import Flask, request, jsonify, render_template, redirect, url_for, session
from datetime import datetime, date
from functools import wraps
from typing import Optional
import json
import os
import logging
import random
import requests
import sqlite3

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__, template_folder='templates')
app.secret_key = 'witch_club_secret_2025'

DB_FILE = '/tmp/witch_club.db'

TELEGRAM_BOT_TOKEN = '8500508012:AAEMuWXEsZsUfiDiOV50xFw928Tn7VUJRH8'
TELEGRAM_CHAT_ID = '-5015136189'
TELEGRAM_CHAT_LINK = 'https://t.me/+S32BT0FT6w0xYTBi'
ADMIN_PASSWORD = 'witch2026'

EMOJIS = ['🔮', '🌙', '🧿', '✨', '🕯️', '🌑', '🧙‍♀️', '🌸', '🕊️', '🌊', '🍂', '❄️', '🌻', '🦉', '🪙', '💫', '⭐', '🔥', '🌿', '💎', '⚡', '🦋']
TITLES = ["Верховная Ведьма", "Ведьма Звёздного Пути", "Ведьма Трав и Эликсиров", "Ведьма Огненного Круга", "Ведьма Лунного Света", "Ведьма Кристаллов", "Ведьма Грозовых Ветров", "Ведьма Превращений"]

def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS surveys (
        id INTEGER PRIMARY KEY,
        name TEXT NOT NULL,
        birthDate TEXT,
        telegramUsername TEXT,
        familyStatus TEXT,
        children TEXT,
        interests TEXT,
        topics TEXT,
        goals TEXT,
        source TEXT,
        useTelegram INTEGER,
        status TEXT DEFAULT 'pending',
        createdAt TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS members (
        id INTEGER PRIMARY KEY,
        name TEXT NOT NULL,
        emoji TEXT,
        title TEXT,
        joinedAt TEXT,
        birthDate TEXT
    )''')
    conn.commit()
    conn.close()

init_db()

def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'admin_logged_in' not in session:
            return redirect(url_for('admin_login'))
        return f(*args, **kwargs)
    return decorated

def send_telegram_message(text: str) -> bool:
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        data = {'chat_id': TELEGRAM_CHAT_ID, 'text': text, 'parse_mode': 'HTML'}
        resp = requests.post(url, json=data, timeout=10)
        print(f"📲 Telegram: {resp.status_code}")
        return resp.status_code == 200
    except Exception as e:
        print(f"❌ Telegram error: {e}")
        return False

def send_welcome_message(name: str, telegram_username: Optional[str]):
    if telegram_username:
        text = f"🎉 <b>Добро пожаловать, {name}!</b>\n\n📱 Присоединяйся:\n{TELEGRAM_CHAT_LINK}"
    else:
        text = f"🎉 <b>Добро пожаловать, {name}!</b>\n\nАдминистратор отправит ссылку на чат."
    send_telegram_message(text)

@app.route('/')
def index_page():
    survey = None
    status = None
    survey_id = session.get('last_survey_id')
    
    if survey_id:
        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        c.execute('SELECT name, status FROM surveys WHERE id = ?', (survey_id,))
        row = c.fetchone()
        conn.close()
        if row:
            survey = {'name': row[0]}
            status = row[1]
    
    return render_template('index.html', profile_survey=survey, profile_status=status)

@app.route('/health')
def health():
    return jsonify({'status': 'ok'})

@app.route('/api/survey', methods=['POST'])
def submit_survey():
    try:
        data = request.json or {}
        name = (data.get('name') or '').strip()
        if not name:
            return jsonify({'error': 'Имя обязательно'}), 400

        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        
        c.execute('''INSERT INTO surveys 
            (name, birthDate, telegramUsername, familyStatus, children, interests, topics, goals, source, useTelegram)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
            (name, data.get('birthDate', ''), data.get('telegramUsername', ''),
             data.get('familyStatus', ''), data.get('children', ''),
             data.get('interests', ''), data.get('topics', ''),
             data.get('goals', ''), data.get('source', ''),
             1 if data.get('useTelegram') == 'yes' else 0))
        
        conn.commit()
        survey_id = c.lastrowid
        conn.close()

        session['last_survey_id'] = survey_id
        
        print(f"✅ Анкета #{survey_id} сохранена: {name}")
        
        use_telegram = data.get('useTelegram') == 'yes'
        survey_text = f"<b>Новая анкета!</b>\n\nИмя: <b>{name}</b>\nID: {survey_id}"
        send_telegram_message(survey_text)
        send_welcome_message(name, data.get('telegramUsername') if use_telegram else None)
        
        return jsonify({'success': True}), 200
    except Exception as e:
        print(f"❌ Error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/members', methods=['GET'])
def api_members():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('SELECT * FROM members')
    rows = c.fetchall()
    conn.close()
    
    members = [{'id': r[0], 'name': r[1], 'emoji': r[2], 'title': r[3], 'joinedAt': r[4], 'birthDate': r[5]} for r in rows]
    return jsonify(members)

@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    error = None
    if request.method == 'POST':
        password = request.form.get('password', '')
        if password == ADMIN_PASSWORD:
            session['admin_logged_in'] = True
            return redirect(url_for('admin_dashboard'))
        error = 'Неверный пароль'
    return render_template('admin_login.html', error=error)

@app.route('/admin/logout')
def admin_logout():
    session.clear()
    return redirect(url_for('index_page'))

@app.route('/admin')
@login_required
def admin_dashboard():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    
    c.execute('SELECT COUNT(*) FROM surveys')
    total_surveys = c.fetchone()[0]
    
    c.execute('SELECT COUNT(*) FROM surveys WHERE status = ?', ('approved',))
    approved = c.fetchone()[0]
    
    c.execute('SELECT COUNT(*) FROM surveys WHERE status = ?', ('pending',))
    pending = c.fetchone()[0]
    
    c.execute('SELECT COUNT(*) FROM members')
    total_members = c.fetchone()[0]
    
    c.execute('SELECT * FROM surveys WHERE status = ? ORDER BY createdAt DESC', ('pending',))
    pending_list = [{'id': r[0], 'name': r[1]} for r in c.fetchall()]
    
    c.execute('SELECT * FROM members')
    members_list = [{'id': r[0], 'name': r[1], 'emoji': r[2], 'title': r[3]} for r in c.fetchall()]
    
    conn.close()
    
    return render_template('admin_dashboard.html',
        total_surveys=total_surveys,
        approved_surveys=approved,
        pending_surveys=pending,
        total_members=total_members,
        pending_list=pending_list,
        members_list=members_list)

@app.route('/api/approve/<int:survey_id>', methods=['POST'])
@login_required
def approve_survey(survey_id):
    try:
        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        
        c.execute('SELECT name, telegramUsername, useTelegram FROM surveys WHERE id = ?', (survey_id,))
        row = c.fetchone()
        if not row:
            return jsonify({'error': 'Not found'}), 404
        
        name, tg_user, use_tg = row
        
        c.execute('''INSERT INTO members (name, emoji, title, joinedAt, birthDate)
                    VALUES (?, ?, ?, ?, ?)''',
                 (name, random.choice(EMOJIS), random.choice(TITLES), 
                  datetime.now().strftime('%Y-%m-%d'), ''))
        
        c.execute('UPDATE surveys SET status = ? WHERE id = ?', ('approved', survey_id))
        conn.commit()
        conn.close()
        
        send_welcome_message(name, tg_user if use_tg else None)
        
        return redirect(url_for('admin_dashboard'))
    except Exception as e:
        print(f"❌ Error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/reject/<int:survey_id>', methods=['POST'])
@login_required
def reject_survey(survey_id):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('UPDATE surveys SET status = ? WHERE id = ?', ('rejected', survey_id))
    conn.commit()
    conn.close()
    return redirect(url_for('admin_dashboard'))

@app.route('/api/remove_member/<int:member_id>', methods=['POST'])
@login_required
def remove_member(member_id):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('DELETE FROM members WHERE id = ?', (member_id,))
    conn.commit()
    conn.close()
    return redirect(url_for('admin_dashboard'))

@app.errorhandler(404)
def not_found(e):
    return render_template('index.html')

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)

