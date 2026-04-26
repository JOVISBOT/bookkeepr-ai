"""Check for JavaScript intercepting clicks"""
import requests

session = requests.Session()
session.post('http://localhost:5000/auth/login', data={
    'email': 'test@bookkeepr.ai',
    'password': 'password123'
})

response = session.get('http://localhost:5000/')
html = response.text

# Check for React or JavaScript that might intercept
if 'react' in html.lower():
    print("React found in HTML")
if 'vue' in html.lower():
    print("Vue found in HTML")
if 'angular' in html.lower():
    print("Angular found in HTML")
if 'javascript' in html.lower():
    print("JavaScript found")
if 'onclick' in html.lower():
    print("onclick handlers found")

# Check for event listeners
if 'addEventListener' in html:
    print("addEventListener found")

print("\nChecking for script tags...")
import re
scripts = re.findall(r'<script[^\u003e]*\u003e(.*?)</script>', html, re.DOTALL)
print(f"Found {len(scripts)} script blocks")
