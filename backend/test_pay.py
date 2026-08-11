import urllib.request, json, urllib.parse, sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

data = urllib.parse.urlencode({'username': 'priya@demo.com', 'password': '123456'}).encode()
req = urllib.request.Request('http://127.0.0.1:8000/api/v1/auth/login', data=data, headers={'Content-Type': 'application/x-www-form-urlencoded'})
resp = urllib.request.urlopen(req, timeout=10)
token = json.loads(resp.read())['accessToken']

messages = ['Gold Facial Kit kitna ka hai', '1', 'Upi']
for msg in messages:
    chat_data = json.dumps({'business_id': 'c5ac0190-cf9e-46e6-a7a9-7d86d15fcba9', 'message': msg, 'session_id': 'pay-e2e', 'customer_name': 'Repair-it'}).encode()
    req2 = urllib.request.Request('http://127.0.0.1:8000/api/v1/chat', data=chat_data, headers={'Content-Type': 'application/json', 'Authorization': 'Bearer ' + token})
    resp2 = urllib.request.urlopen(req2, timeout=30)
    result = json.loads(resp2.read())
    print(f'Q: {msg}')
    print(f'A: {result.get("reply", "NO")}')
    print()
