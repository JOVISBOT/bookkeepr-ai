"""Test dashboard with session"""
import requests

session = requests.Session()

# Get login page first
response = session.get('http://localhost:5000/auth/login')
print(f"Login page status: {response.status_code}")

# Check if there's a CSRF token
if 'csrf_token' in response.text:
    print("CSRF token found")
else:
    print("No CSRF token")

# Try POST with content-type
headers = {'Content-Type': 'application/x-www-form-urlencoded'}
data = 'email=test@bookkeepr.ai&password=password123'

response = session.post('http://localhost:5000/auth/login', data=data, headers=headers, allow_redirects=True)
print(f"\nLogin POST status: {response.status_code}")
print(f"URL: {response.url}")

# Check dashboard
response = session.get('http://localhost:5000/')
print(f"\nDashboard: {response.status_code}, Length: {len(response.text)}")

if 'dashboard.css' in response.text:
    print("NEW DASHBOARD!")
elif 'BookKeepr AI' in response.text:
    print("Old dashboard still showing")
else:
    print(response.text[:500])
