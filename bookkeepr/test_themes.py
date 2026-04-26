"""Test all links"""
import requests

session = requests.Session()

# Login
session.post('http://localhost:5000/auth/login', data={
    'email': 'test@bookkeepr.ai',
    'password': 'password123'
})

pages = [
    '/dashboard/transactions',
    '/dashboard/accounts', 
    '/dashboard/reports',
    '/dashboard/settings'
]

for page in pages:
    response = session.get(f'http://localhost:5000{page}')
    has_blue_theme = 'dashboard.css' in response.text
    has_old_theme = 'tailwindcss' in response.text or 'gray-50' in response.text
    status = "BLUE THEME" if has_blue_theme else ("OLD THEME" if has_old_theme else "UNKNOWN")
    print(f"{page}: {status}")
