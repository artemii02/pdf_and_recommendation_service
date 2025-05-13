import redis
import os
import json

REDIS_HOST = os.getenv('REDIS_HOST', 'localhost')
REDIS_PORT = int(os.getenv('REDIS_PORT', 6379))
REDIS_DB = int(os.getenv('REDIS_DB', 0))
REDIS_PASSWORD = os.getenv('REDIS_PASSWORD', 'your_redis_password')

r = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, db=REDIS_DB, password=REDIS_PASSWORD)

found = False
print('--- Все ключи, связанные с рекомендациями и PDF ---')
for key in r.scan_iter(match='recommendations:*'):
    found = True
    value = r.get(key)
    print(f'Ключ: {key.decode() if isinstance(key, bytes) else key}')
    try:
        print('Значение:', json.dumps(json.loads(value), ensure_ascii=False, indent=2))
    except Exception:
        print('Значение:', value)
    print('-' * 40)
for key in r.scan_iter(match='pdf:*'):
    found = True
    value = r.get(key)
    print(f'Ключ: {key.decode() if isinstance(key, bytes) else key}')
    try:
        print('Значение:', json.dumps(json.loads(value), ensure_ascii=False, indent=2))
    except Exception:
        print('Значение:', value)
    print('-' * 40)
if not found:
    print('Нет ключей с recommendations:* или pdf:*. Вывожу все ключи Redis:')
    for key in r.scan_iter(match='*'):
        value = r.get(key)
        print(f'Ключ: {key.decode() if isinstance(key, bytes) else key}')
        print('Значение:', value)
        print('-' * 40)
print('--- Конец вывода ---') 