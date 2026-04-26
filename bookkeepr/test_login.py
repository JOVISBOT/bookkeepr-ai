"""Test login flow"""
import requests

session = requests.Session()

# Test login
login_data = {
    'email': 'test@bookkeepr.ai',
    'password': 'password123',
    'remember_me': 'on'
}

response = session.post('http://localhost:5000/auth/login', data=login_data, allow_redirects=True)
print("Login status:", response.status_code)
print("URL after:", response.url)

# Check dashboard
response = session.get('http://localhost:5000/')
print("\nDashboard:", response.status_code, "Length:", len(response.text))

if 'dashboard.css' in response.text:
    print("NEW BLUE DASHBOARD!")
elif 'Sign In' in response.text:
    print("Still on login page")
else:
    print("Preview:", response.text[:500])
