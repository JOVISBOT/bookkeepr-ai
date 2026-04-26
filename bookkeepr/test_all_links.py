"""Test all links after restart"""
import subprocess
import time
import requests

# Kill and restart
subprocess.run(['taskkill', '/F', '/IM', 'python.exe'], capture_output=True)
time.sleep(2)

proc = subprocess.Popen(
    ['python', 'run.py'],
    cwd=r'C:\Users\jovis\.openclaw\workspace\bookkeepr\app',
    creationflags=subprocess.CREATE_NEW_CONSOLE
)

time.sleep(5)

session = requests.Session()

# Login
session.post('http://localhost:5000/auth/login', data={
    'email': 'test@bookkeepr.ai',
    'password': 'password123'
})

# Test all links
links = ['/dashboard/transactions', '/dashboard/accounts', '/dashboard/reports', '/dashboard/settings']

print("Testing all links:")
for link in links:
    response = session.get(f'http://localhost:5000{link}')
    status = "OK" if response.status_code == 200 else f"ERROR {response.status_code}"
    print(f"  {link}: {status}")
