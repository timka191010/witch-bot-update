from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
import json
import os
from datetime import datetime
from pathlib import Path

app = Flask(__name__, static_folder='public', static_url_path='')
CORS(app)

# Папка для данных
DATA_DIR = Path('data')
DATA_DIR.mkdir(exist_ok=True)

SURVEYS_FILE = DATA_DIR / 'surveys.json'
MEMBERS_FILE = Path('public/members.json')

# === ЗАГРУЗКА ДАННЫХ ===
def load_surveys():
    if SURVEYS_FILE.exists():
        with open(SURVEYS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return []

def save_surveys(surveys):
    with open(SURVEYS_FILE, 'w', encoding='utf-8') as f:
        json.dump(surveys, f, ensure_ascii=False, indent=2)

def load_members():
    if MEMBERS_FILE.exists():
        with open(MEMBERS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

# === МАРШРУТЫ ===

@app.route('/')
def index():
    return app.send_static_file('index.html')

@app.route('/members.json')
def get_members():
    members = load_members()
    return jsonify(members)

@app.route('/api/members', methods=['GET'])
def api_members():
    members = load_members()
    members_list = list(members.values())
    return jsonify(members_list)

@app.route('/api/survey', methods=['POST'])
def save_survey():
    try:
        data = request.get_json()
        
        if not data.get('name'):
            return jsonify({'error': 'Имя обязательно'}), 400

        # Проверяем минимум данных
        if not data.get('name'):
            return jsonify({'error': 'Заполните имя'}), 400

        # Создаём запись
        survey = {
            'id': datetime.now().isoformat(),
            'name': data.get('name'),
            'birthDate': data.get('birthDate'),
            'telegramUsername': data.get('telegramUsername'),
            'familyStatus': data.get('familyStatus'),
            'children': data.get('children'),
            'interests': data.get('interests'),
            'topics': data.get('topics'),
            'goals': data.get('goals'),
            'source': data.get('source'),
            'useTelegram': data.get('useTelegram'),
            'createdAt': datetime.now().isoformat(),
            'status': 'pending'
        }

        # Сохраняем
        surveys = load_surveys()
        surveys.append(survey)
        save_surveys(surveys)

        print(f"✅ Анкета сохранена: {survey['name']}")
        return jsonify({'success': True, 'message': 'Анкета отправлена'}), 200

    except Exception as e:
        print(f"❌ Ошибка: {str(e)}")
        return jsonify({'error': f'Ошибка сервера: {str(e)}'}), 500

@app.route('/admin')
def admin():
    return render_template('admin.html')

@app.route('/api/surveys', methods=['GET'])
def get_surveys():
    surveys = load_surveys()
    return jsonify(surveys)

@app.route('/api/survey/<survey_id>', methods=['PUT'])
def update_survey(survey_id):
    try:
        data = request.get_json()
        surveys = load_surveys()
        
        for survey in surveys:
            if survey['id'] == survey_id:
                survey['status'] = data.get('status', 'pending')
                save_surveys(surveys)
                return jsonify({'success': True}), 200
        
        return jsonify({'error': 'Анкета не найдена'}), 404

    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
