"""Restart server and test charts"""
import subprocess
import time
import requests

# Kill existing server
subprocess.run(['taskkill', '/F', '/IM', 'python.exe'], capture_output=True)
time.sleep(3)

# Start server
proc = subprocess.Popen(
    ['python', 'run.py'],
    cwd=r'C:\Users\jovis\.openclaw\workspace\bookkeepr\app',
    creationflags=subprocess.CREATE_NEW_CONSOLE
)

time.sleep(5)

# Test endpoints
session = requests.Session()

# Login
session.post('http://localhost:5000/auth/login', data={
    'email': 'test@bookkeepr.ai',
    'password': 'password123'
})

# Test chart data endpoints
endpoints = [
    '/api/v1/data/pnl',
    '/api/v1/data/balance',
    '/api/v1/data/expenses',
    '/api/v1/reports/pnl',
    '/api/v1/reports/balance'
]

print("Testing chart and report endpoints:")
for endpoint in endpoints:
    try:
        response = session.get(f'http://localhost:5000{endpoint}')
        status = "OK" if response.status_code == 200 else f"ERROR {response.status_code}"
        print(f"  {endpoint}: {status}")
    except Exception as e:
        print(f"  {endpoint}: FAILED - {e}")

print("\nServer restarted successfully!")
