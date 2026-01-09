import json
import os
from datetime import datetime

def main(request):
    members_file = 'api/members.json'
    
    # Создаем директорию если нет
    if not os.path.exists('api'):
        os.makedirs('api')
    
    # Создаем пустой файл если нет
    if not os.path.exists(members_file):
        with open(members_file, 'w', encoding='utf-8') as f:
            json.dump([], f, ensure_ascii=False)
    
    # GET - читаем участниц
    if request.method == 'GET':
        try:
            with open(members_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            return {
                'statusCode': 200,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps(data, ensure_ascii=False)
            }
        except Exception as e:
            return {
                'statusCode': 500,
                'body': json.dumps({'error': str(e)})
            }
    
    # POST - добавляем новую анкету
    elif request.method == 'POST':
        try:
            body = json.loads(request.body) if isinstance(request.body, str) else request.body
            
            # Читаем существующих участниц
            with open(members_file, 'r', encoding='utf-8') as f:
                members = json.load(f)
            
            # Добавляем новую
            new_member = {
                'id': len(members) + 1,
                'name': body.get('name'),
                'birthDate': body.get('birthDate'),
                'telegram': body.get('telegram'),
                'maritalStatus': body.get('maritalStatus'),
                'children': body.get('children'),
                'hobbies': body.get('hobbies'),
                'topics': body.get('topics'),
                'goal': body.get('goal'),
                'source': body.get('source'),
                'agreement': body.get('agreement'),
                'createdAt': datetime.now().isoformat(),
                'emoji': '🧙‍♀️',
                'title': 'Новая участница',
                'bio': body.get('hobbies', '')[:50]
            }
            
            members.append(new_member)
            
            # Сохраняем
            with open(members_file, 'w', encoding='utf-8') as f:
                json.dump(members, f, ensure_ascii=False, indent=2)
            
            return {
                'statusCode': 200,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({'status': 'success', 'message': 'Анкета добавлена'}, ensure_ascii=False)
            }
        except Exception as e:
            return {
                'statusCode': 400,
                'body': json.dumps({'error': str(e)}, ensure_ascii=False)
            }
    
    # OPTIONS для CORS
    elif request.method == 'OPTIONS':
        return {
            'statusCode': 200,
            'headers': {
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
                'Access-Control-Allow-Headers': 'Content-Type'
            }
        }
