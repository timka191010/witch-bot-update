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
                    bio=m.get('birthDate', '')  # Сохраняем дату рождения в bio
                )
                db.session.add(member)
                count += 1
        
        db.session.commit()
        return jsonify({'status': 'success', 'loaded': count})
    
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)})
