import requests

res = requests.post('http://127.0.0.1:8000/auth/register', json={'username': 'testuser2', 'email': 'test2@example.com', 'password': 'password123'})
print('Register:', res.status_code, res.text)

res2 = requests.post('http://127.0.0.1:8000/auth/token', data={'username': 'test2@example.com', 'password': 'password123'})
print('Token:', res2.status_code, res2.text)

token = res2.json().get('access_token')

if token:
    res3 = requests.get('http://127.0.0.1:8000/auth/me', headers={'Authorization': 'Bearer {}'.format(token)})
    print('Me:', res3.status_code, res3.text)
