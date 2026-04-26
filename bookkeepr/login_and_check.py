"""Login and check dashboard"""
import requests

session = requests.Session()

# Login
login_data = {
    'email': 'test@bookkeepr.ai',
    'password': 'password123'
}

response = session.post('http://localhost:5000/auth/login', data=login_data, allow_redirects=True)
print(f"Login status: {response.status_code}")
print(f"URL after login: {response.url}")

# Now check dashboard
response = session.get('http://localhost:5000/')
print(f"\nDashboard status: {response.status_code}")
print(f"Length: {len(response.text)} bytes")

if 'dashboard.css' in response.text:
    print("NEW DASHBOARD FOUND!")
elif 'Sign In' in response.text:
    print("Still showing login page")
else:
    print("Response preview:")
    print(response.text[:800])
