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
    return render_template('admin_dashboard.html')

@app.route('/admin/login')
def admin_login():
    return render_template('admin_login.html')

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

@app.route('/api/admin/surveys/pending', methods=['GET'])
def get_pending_surveys():
    try:
        surveys = load_surveys()
        pending = [s for s in surveys if s.get('status') == 'pending']
        
        # Преобразуем в формат для дашборда
        formatted = []
        for s in pending:
            formatted.append({
                'id': s['id'],
                'name': s.get('name', ''),
                'birth_date': s.get('birthDate', ''),
                'telegram': s.get('telegramUsername', ''),
                'about': s.get('interests', '')
            })
        
        return jsonify({'surveys': formatted}), 200
    except Exception as e:
        print(f'❌ Ошибка: {e}')
        return jsonify({'surveys': []}), 200

@app.route('/api/admin/stats', methods=['GET'])
def get_admin_stats():
    try:
        surveys = load_surveys()
        
        try:
            with open('public/members.json', 'r', encoding='utf-8') as f:
                members = json.load(f)
        except:
            members = {}
        
        total_surveys = len(surveys)
        pending_surveys = len([s for s in surveys if s.get('status') == 'pending'])
        approved_surveys = len([s for s in surveys if s.get('status') == 'approved'])
        total_members = len(members)
        
        return jsonify({
            'stats': {
                'total_surveys': total_surveys,
                'pending_surveys': pending_surveys,
                'approved_surveys': approved_surveys,
                'total_members': total_members
            }
        }), 200
    except Exception as e:
        print(f'❌ Ошибка статистики: {e}')
        return jsonify({
            'stats': {
                'total_surveys': 0,
                'pending_surveys': 0,
                'approved_surveys': 0,
                'total_members': 0
            }
        }), 200

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

@app.route('/api/surveys/<survey_id>/approve', methods=['POST'])
def approve_survey(survey_id):
    try:
        surveys = load_surveys()
        survey_data = None
        
        # Найди анкету
        for survey in surveys:
            if survey['id'] == survey_id:
                survey_data = survey
                survey['status'] = 'approved'
                break
        
        if not survey_data:
            return jsonify({'error': 'Анкета не найдена'}), 404
        
        # Загрузи участников
        try:
            with open('public/members.json', 'r', encoding='utf-8') as f:
                members = json.load(f)
        except:
            members = {}
        
        # Добавь новую участницу (используй ID анкеты)
        member_id = survey_id
        members[member_id] = {
            'id': member_id,
            'name': survey_data.get('name', ''),
            'title': '🆕 Новенькая',
            'emoji': '✨',
            'birth_date': survey_data.get('birthDate', ''),
            'telegram': survey_data.get('telegramUsername', '')
        }
        
        # Сохрани обратно
        with open('public/members.json', 'w', encoding='utf-8') as f:
            json.dump(members, f, ensure_ascii=False, indent=2)
        
        # Сохрани обновленные анкеты
        save_surveys(surveys)
        
        print(f'✅ Участница добавлена: {survey_data["name"]}')
        return jsonify({'success': True}), 200
        
    except Exception as e:
        print(f'❌ Ошибка approve: {e}')
        return jsonify({'error': str(e)}), 500

@app.route('/api/surveys/<survey_id>/reject', methods=['POST'])
def reject_survey(survey_id):
    try:
        surveys = load_surveys()
        surveys = [s for s in surveys if s['id'] != survey_id]
        save_surveys(surveys)
        
        print(f'✅ Анкета отклонена: {survey_id}')
        return jsonify({'success': True}), 200
    except Exception as e:
        print(f'❌ Ошибка reject: {e}')
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

@app.route('/api/members/<member_id>/title', methods=['PUT'])
def update_member_title(member_id):
    try:
        data = request.get_json()
        new_title = data.get('title', '')
        
        with open('public/members.json', 'r', encoding='utf-8') as f:
            members = json.load(f)
        
        if member_id in members:
            members[member_id]['title'] = new_title
            
            with open('public/members.json', 'w', encoding='utf-8') as f:
                json.dump(members, f, ensure_ascii=False, indent=2)
            
            print(f'✅ Титул обновлен: {members[member_id]["name"]} -> {new_title}')
            return jsonify({'success': True}), 200
        
        return jsonify({'error': 'Участница не найдена'}), 404
    except Exception as e:
        print(f'❌ Ошибка update title: {e}')
        return jsonify({'error': str(e)}), 500

@app.route('/api/members/<member_id>', methods=['DELETE'])
def delete_member(member_id):
    try:
        with open('public/members.json', 'r', encoding='utf-8') as f:
            members = json.load(f)
        
        if member_id in members:
            del members[member_id]
            
            with open('public/members.json', 'w', encoding='utf-8') as f:
                json.dump(members, f, ensure_ascii=False, indent=2)
            
            print(f'✅ Участница удалена')
            return jsonify({'success': True}), 200
        
        return jsonify({'error': 'Участница не найдена'}), 404
    except Exception as e:
        print(f'❌ Ошибка delete: {e}')
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
