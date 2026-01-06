from flask import Flask, request, jsonify, render_template, redirect, url_for, session
from datetime import datetime, date
from functools import wraps
from typing import Optional
import json
import os
import logging
import random
import requests

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.secret_key = 'witch_club_secret_2025'

SURVEYS_FILE = 'surveys.json'
MEMBERS_FILE = 'members.json'
ADMIN_PASSWORD = 'witch2026'

TELEGRAM_BOT_TOKEN = '8500508012:AAEMuWXEsZsUfiDiOV50xFw928Tn7VUJRH8'
TELEGRAM_CHAT_ID = '-5015136189'
TELEGRAM_CHAT_LINK = 'https://t.me/+S32BT0FT6w0xYTBi'

EMOJIS = [
    '🔮', '🌙', '🧿', '✨', '🕯️', '🌑', '🧙‍♀️', '🌸', '🕊️', '🌊',
    '🍂', '❄️', '🌻', '🦉', '🪙', '💫', '⭐', '🔥', '🌿', '💎', '⚡', '🦋'
]

TITLES = [
    "Верховная Ведьма",
    "Ведьма Звёздного Пути",
    "Ведьма Трав и Эликсиров",
    "Ведьма Огненного Круга",
    "Ведьма Лунного Света",
    "Ведьма Кристаллов",
    "Ведьма Грозовых Ветров",
    "Ведьма Превращений",
]


def load_json(filepath):
    try:
        if os.path.exists(filepath):
            with open(filepath, 'r', encoding='utf-8') as f:
                return json.load(f)
    except Exception as e:
        logger.error(f"Error loading {filepath}: {e}")
    return {}


def save_json(filepath, data):
    try:
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        logger.error(f"Error saving {filepath}: {e}")
        return False


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
        print(resp.status_code, resp.text)
        return resp.status_code == 200
    except Exception as e:
        logger.error(f"Telegram send error: {e}")
        return False


def send_welcome_message(name: str, telegram_username: Optional[str]):
    if telegram_username:
        text = (
            f"🎉 <b>Добро пожаловать, {name}!</b>\n\n"
            f"Ты принята в клуб <b>«Ведьмы не стареют»</b>.\n\n"
            f"📱 Присоединяйся к чату:\n{TELEGRAM_CHAT_LINK}"
        )
    else:
        text = (
            f"🎉 <b>Добро пожаловать, {name}!</b>\n\n"
            f"Ты принята в клуб <b>«Ведьмы не стареют»</b>.\n\n"
            "Администратор свяжется с тобой и отправит ссылку на чат."
        )
    send_telegram_message(text)


def format_survey_for_admin(survey: dict, use_telegram: bool) -> str:
    lines = [
        "<b>Новая анкета в клуб</b>",
        "",
        f"Имя: <b>{survey['name']}</b>",
        f"Дата рождения: {survey.get('birthDate') or '—'}",
        f"Telegram: @{survey.get('telegramUsername') or '—'}",
        f"Семейное положение: {survey.get('familyStatus') or '—'}",
        f"Дети: {survey.get('children') or '—'}",
        "",
        f"Увлечения: {survey.get('interests') or '—'}",
        f"Темы: {survey.get('topics') or '—'}",
        f"Цель: {survey.get('goals') or '—'}",
        "",
        f"Источник: {survey.get('source') or '—'}",
        f"ID анкеты: {survey['id']}",
    ]
    if use_telegram:
        lines += [
            "",
            "✅ Отметила, что готова общаться в Telegram.",
            f"Ссылка на чат: {TELEGRAM_CHAT_LINK}",
        ]
    return "\n".join(lines)


@app.route('/')
def index_page():
    surveys = load_json(SURVEYS_FILE)
    survey = None
    status = None

    survey_id = session.get('last_survey_id')
    if isinstance(surveys, dict) and survey_id and survey_id in surveys:
        survey = surveys[survey_id]
        status = survey.get('status')

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

        surveys = load_json(SURVEYS_FILE)
        if not isinstance(surveys, dict):
            surveys = {}

        survey_id = str(len(surveys) + 1)
        use_telegram = (data.get('useTelegram') == 'yes')

        surveys[survey_id] = {
            'id': survey_id,
            'name': name,
            'birthDate': data.get('birthDate', ''),
            'telegramUsername': (data.get('telegramUsername') or '').strip(),
            'familyStatus': data.get('familyStatus', ''),
            'children': data.get('children', ''),
            'interests': data.get('interests', ''),
            'topics': data.get('topics', ''),
            'goals': data.get('goals', ''),
            'source': data.get('source', ''),
            'useTelegram': use_telegram,
            'status': 'pending',
            'createdAt': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        }

        if not save_json(SURVEYS_FILE, surveys):
            return jsonify({'error': 'Save failed'}), 500

        session['last_survey_id'] = survey_id

        send_telegram_message(format_survey_for_admin(surveys[survey_id], use_telegram))
        return jsonify({'success': True, 'survey': surveys[survey_id]}), 200
    except Exception as e:
        logger.error(f"Error submitting survey: {e}")
        return jsonify({'error': 'Server error'}), 500


@app.route('/api/members', methods=['GET'])
def api_members():
    members = load_json(MEMBERS_FILE)
    if isinstance(members, dict):
        return jsonify(list(members.values()))
    return jsonify(members or [])


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
    surveys = load_json(SURVEYS_FILE)
    members = load_json(MEMBERS_FILE)

    surveys_list = list(surveys.values()) if isinstance(surveys, dict) else (surveys or [])
    members_list = list(members.values()) if isinstance(members, dict) else (members or [])

    pending = [s for s in surveys_list if s.get('status') == 'pending']
    approved = [s for s in surveys_list if s.get('status') == 'approved']

    return render_template(
        'admin_dashboard.html',
        total_surveys=len(surveys_list),
        approved_surveys=len(approved),
        pending_surveys=len(pending),
        total_members=len(members_list),
        pending_list=pending,
        members_list=members_list
    )


@app.route('/admin/stats')
@login_required
def admin_stats():
    surveys = load_json(SURVEYS_FILE)
    if not isinstance(surveys, dict):
        surveys = {}
    surveys_list = list(surveys.values())

    stats = {
        'total': len(surveys_list),
        'approved': len([s for s in surveys_list if s.get('status') == 'approved']),
        'pending': len([s for s in surveys_list if s.get('status') == 'pending']),
        'rejected': len([s for s in surveys_list if s.get('status') == 'rejected']),
    }

    members = load_json(MEMBERS_FILE)
    if not isinstance(members, dict):
        members = {}
    stats['members_count'] = len(members)

    stats['married'] = len([s for s in surveys_list if s.get('familyStatus') == 'married'])
    stats['single'] = len([s for s in surveys_list if s.get('familyStatus') == 'single'])

    stats['with_kids'] = len([s for s in surveys_list if s.get('children')])
    stats['no_kids'] = stats['total'] - stats['with_kids']

    sources = {}
    for s in surveys_list:
        src = s.get('source') or 'Не указано'
        sources[src] = sources.get(src, 0) + 1
    stats['sources'] = sources

    return render_template('admin_stats.html', stats=stats)


@app.route('/api/approve/<survey_id>', methods=['POST'])
@login_required
def approve_survey(survey_id):
    try:
        surveys = load_json(SURVEYS_FILE)
        if not isinstance(surveys, dict):
            return jsonify({'error': 'Invalid surveys data'}), 400

        survey = surveys.get(survey_id)
        if not survey:
            return jsonify({'error': 'Not found'}), 404

        members = load_json(MEMBERS_FILE)
        if not isinstance(members, dict):
            members = {}

        member_id = str(len(members) + 1)
        members[member_id] = {
            'id': member_id,
            'name': survey['name'],
            'emoji': random.choice(EMOJIS),
            'title': random.choice(TITLES),
            'joinedAt': datetime.now().strftime('%Y-%m-%d'),
            'birthDate': survey.get('birthDate', '')
        }

        survey['status'] = 'approved'

        save_json(SURVEYS_FILE, surveys)
        save_json(MEMBERS_FILE, members)

        send_welcome_message(survey['name'], survey.get('telegramUsername'))

        return redirect(url_for('admin_dashboard'))
    except Exception as e:
        logger.error(f"Error approving survey: {e}")
        return jsonify({'error': 'Server error'}), 500


@app.route('/api/reject/<survey_id>', methods=['POST'])
@login_required
def reject_survey(survey_id):
    surveys = load_json(SURVEYS_FILE)
    if not isinstance(surveys, dict) or survey_id not in surveys:
        return jsonify({'error': 'Not found'}), 404

    surveys[survey_id]['status'] = 'rejected'
    save_json(SURVEYS_FILE, surveys)
    return redirect(url_for('admin_dashboard'))


@app.route('/api/remove_member/<member_id>', methods=['POST'])
@login_required
def remove_member(member_id):
    members = load_json(MEMBERS_FILE)
    if not isinstance(members, dict) or member_id not in members:
        return jsonify({'error': 'Not found'}), 404

    members.pop(member_id)
    save_json(MEMBERS_FILE, members)
    return redirect(url_for('admin_dashboard'))


@app.route('/api/update_title/<member_id>', methods=['POST'])
@login_required
def update_title(member_id):
    members = load_json(MEMBERS_FILE)
    if not isinstance(members, dict) or member_id not in members:
        return jsonify({'error': 'Not found'}), 404

    new_title = request.form.get('title', '').strip()
    if not new_title:
        return jsonify({'error': 'Empty title'}), 400

    members[member_id]['title'] = new_title
    save_json(MEMBERS_FILE, members)
    return redirect(url_for('admin_dashboard'))


@app.route('/api/clear_surveys', methods=['POST'])
@login_required
def clear_surveys():
    save_json(SURVEYS_FILE, {})
    session.pop('last_survey_id', None)
    return redirect(url_for('admin_dashboard'))


def parse_birth(birth_str: str):
    try:
        d, m, _y = birth_str.split('.')
        return int(d), int(m)
    except Exception:
        return None


@app.route('/api/next_birthday')
@login_required
def next_birthday():
    members = load_json(MEMBERS_FILE)
    if not isinstance(members, dict):
        members = {}

    today = date.today()
    best = None  # (days_diff, member)

    for m in members.values():
        bd_str = m.get('birthDate') or ''
        parsed = parse_birth(bd_str)
        if not parsed:
            continue
        d, mth = parsed
        try:
            dt = date(today.year, mth, d)
        except ValueError:
            continue
        if dt < today:
            dt = date(today.year + 1, mth, d)
        diff = (dt - today).days
        if best is None or diff < best[0]:
            best = (diff, m)

    if not best:
        return jsonify({'hasBirthday': False})

    diff, member = best
    return jsonify({'hasBirthday': True, 'days': diff, 'member': member})


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=8080)
