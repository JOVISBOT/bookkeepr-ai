"""Check transactions route directly"""
import requests

session = requests.Session()

# Login
session.post('http://localhost:5000/auth/login', data={
    'email': 'test@bookkeepr.ai',
    'password': 'password123'
})

# Get transactions
response = session.get('http://localhost:5000/dashboard/transactions')
print(f"Status: {response.status_code}")
print(f"URL: {response.url}")
print(f"Length: {len(response.text)}")
print(f"\nContains 'Transactions': {'Transactions' in response.text}")
print(f"Contains 'Dashboard': {'Dashboard' in response.text}")
