import json
import os

def main(request):
    # Читаем твой members.json
    with open('api/members.json', 'r', encoding='utf-8') as f:
        data = json.load(f)
    return {
        'statusCode': 200,
        'headers': {'Content-Type': 'application/json'},
        'body': json.dumps(data)
    }
