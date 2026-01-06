from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import json
import os
from datetime import datetime
from pathlib import Path

app = Flask(__name__, static_folder='public', static_url_path='')
CORS(app)

app.config['JSON_AS_ASCII'] = False

# Папки
DATA_DIR = Path('data')
DATA_DIR.mkdir(exist_ok=True)
SURVEYS_FILE = DATA_DIR / 'surveys.json'

def load_surveys():
    if SURVEYS_FILE.exists():
        try:
            with open(SURVEYS_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return []
    return []

def save_surveys(surveys):
    with open(SURVEYS_FILE, 'w', encoding='utf-8') as f:
        json.dump(surveys, f, ensure_ascii=False, indent=2)

# === ГЛАВНАЯ ===
@app.route('/')
def index():
    return send_from_directory('public', 'index.html')

# === СТАТИКА ===
@app.route('/<path:path>')
def serve_static(path):
    try:
        return send_from_directory('public', path)
    except:
        return send_from_directory('public', 'index.html')

# === API ===
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
            return jsonify({'error': 'Name required'}), 400

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

        print(f'✅ Survey saved: {survey["name"]}')
        return jsonify({'success': True}), 200

    except Exception as e:
        print(f'❌ Error: {str(e)}')
        return jsonify({'error': str(e)}), 500

@app.errorhandler(404)
def not_found(e):
    return send_from_directory('public', 'index.html')

@app.errorhandler(500)
def server_error(e):
    return jsonify({'error': 'Server error'}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
