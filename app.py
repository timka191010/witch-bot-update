from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import json
import os
from datetime import datetime
from pathlib import Path

app = Flask(__name__, template_folder='api/templates')
CORS(app)

app.config['JSON_AS_ASCII'] = False

# Папки
DATA_DIR = Path('data')
DATA_DIR.mkdir(exist_ok=True)
SURVEYS_FILE = DATA_DIR / 'surveys.json'

def load_surveys():
    if SURVEYS_FILE.exists():
        with open(SURVEYS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return []

def save_surveys(surveys):
    with open(SURVEYS_FILE, 'w', encoding='utf-8') as f:
        json.dump(surveys, f, ensure_ascii=False, indent=2)

# === ГЛАВНАЯ СТРАНИЦА ===
@app.route('/')
def index():
    return render_template('index.html')

# === АДМИНКА ===
@app.route('/admin')
def admin_page():
    return render_template('admin.html')

# === API ===
@app.route('/members.json')
def get_members_json():
    try:
        with open('public/members.json', 'r', encoding='utf-8') as f:
            return jsonify(json.load(f))
    except:
        return jsonify({})

@app.route('/api/members', methods=['GET'])
def api_members():
    try:
        with open('public/members.json', 'r', encoding='utf-8') as f:
            members = json.load(f)
        return jsonify(list(members.values()))
    except:
        return jsonify([])

@app.route('/api/survey', methods=['POST'])
def save_survey():
    try:
        data = request.get_json()
        
        if not data or not data.get('name'):
            return jsonify({'error': 'Имя обязательно'}), 400

        survey = {
            'id': datetime.now().isoformat(),
            'name': data.get('name', ''),
            'birthDate': data.get('birthDate', ''),
            'telegramUsername': data.get('telegramUsername', ''),
            'familyStatus': data.get('familyStatus', ''),
            'children': data.get('children', ''),
            'interests': data.get('interests', ''),
            'topics': data.get('topics', ''),
            'goals': data.get('goals', ''),
            'source': data.get('source', ''),
            'useTelegram': data.get('useTelegram', 'no'),
            'createdAt': datetime.now().isoformat(),
            'status': 'pending'
        }

        surveys = load_surveys()
        surveys.append(survey)
        save_surveys(surveys)

        print(f'✅ Анкета сохранена: {survey["name"]}')
        return jsonify({'success': True}), 200

    except Exception as e:
        print(f'❌ Ошибка: {str(e)}')
        return jsonify({'error': str(e)}), 500

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
        
        return jsonify({'error': 'Не найдена'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/survey/<survey_id>', methods=['DELETE'])
def delete_survey(survey_id):
    try:
        surveys = load_surveys()
        surveys = [s for s in surveys if s['id'] != survey_id]
        save_surveys(surveys)
        return jsonify({'success': True}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.errorhandler(404)
def not_found(e):
    return render_template('index.html')

@app.errorhandler(500)
def server_error(e):
    return jsonify({'error': 'Server error'}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port, debug=False)
