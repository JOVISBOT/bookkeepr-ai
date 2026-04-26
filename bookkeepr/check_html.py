"""Check actual HTML being served"""
import requests

session = requests.Session()

# Login
session.post('http://localhost:5000/auth/login', data={
    'email': 'test@bookkeepr.ai',
    'password': 'password123'
})

# Get dashboard
response = session.get('http://localhost:5000/')
html = response.text

# Find href links
import re
links = re.findall(r'href="([^"]+)"', html)
print("Links found in HTML:")
for link in links:
    if 'transaction' in link.lower() or 'account' in link.lower() or 'report' in link.lower() or 'setting' in link.lower():
        print(f"  {link}")
