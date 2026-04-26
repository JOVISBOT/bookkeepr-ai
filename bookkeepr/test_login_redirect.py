"""Test login and redirect"""
import requests

session = requests.Session()

# Get login page first
response = session.get('http://localhost:5000/auth/login')
print(f"Login page: {response.status_code}")

# Post login
login_data = {
    'email': 'test@bookkeepr.ai',
    'password': 'password123'
}

response = session.post('http://localhost:5000/auth/login', data=login_data, allow_redirects=True)
print(f"After login: {response.status_code}")
print(f"URL: {response.url}")
print(f"History: {[r.status_code for r in response.history]}")

# Check if logged in by accessing dashboard
response = session.get('http://localhost:5000/')
print(f"\nDashboard: {response.status_code}")
print(f"URL: {response.url}")
print(f"Contains 'test': {'test' in response.text}")
print(f"Contains 'Dashboard': {'Dashboard' in response.text}")

# Now try transactions
response = session.get('http://localhost:5000/dashboard/transactions')
print(f"\nTransactions: {response.status_code}")
print(f"URL: {response.url}")
print(f"Contains 'Transactions': {'Transactions' in response.text}")
