"""Check server logs"""
import requests

# Test with debug
session = requests.Session()

# Get login page first
response = session.get('http://localhost:5000/auth/login')
print("GET login page:", response.status_code)

# Now POST
try:
    response = session.post(
        'http://localhost:5000/auth/login',
        data={'email': 'test@bookkeepr.ai', 'password': 'password123'},
        allow_redirects=False
    )
    print("POST login:", response.status_code)
    print("Headers:", dict(response.headers))
    if response.status_code != 302:
        print("Response:", response.text[:1000])
except Exception as e:
    print("Error:", e)
