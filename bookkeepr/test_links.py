"""Test all dashboard links"""
import requests

session = requests.Session()

# Login first
login_data = {
    'email': 'test@bookkeepr.ai',
    'password': 'password123'
}

session.post('http://localhost:5000/auth/login', data=login_data)

links = ['/transactions', '/accounts', '/reports', '/settings']

for link in links:
    response = session.get(f'http://localhost:5000{link}')
    status = "OK" if response.status_code == 200 else f"ERROR {response.status_code}"
    print(f"{link}: {status}")
