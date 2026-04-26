"""Test chart endpoints"""
import requests

session = requests.Session()

# Login
session.post('http://localhost:5000/auth/login', data={
    'email': 'test@bookkeepr.ai',
    'password': 'password123'
})

# Test chart data
endpoints = [
    '/api/v1/data/pnl',
    '/api/v1/data/balance', 
    '/api/v1/data/expenses'
]

for endpoint in endpoints:
    try:
        response = session.get(f'http://localhost:5000{endpoint}')
        if response.status_code == 200:
            data = response.json()
            print(f"{endpoint}: OK")
            print(f"  Keys: {list(data.keys())}")
        else:
            print(f"{endpoint}: ERROR {response.status_code}")
    except Exception as e:
        print(f"{endpoint}: FAILED - {e}")
