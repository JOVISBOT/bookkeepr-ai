"""Restart server and test full flow"""
import subprocess
import time
import requests

# Kill existing Python processes
subprocess.run(['taskkill', '/F', '/IM', 'python.exe'], capture_output=True)
time.sleep(2)

# Start server
proc = subprocess.Popen(
    ['python', 'run.py'],
    cwd=r'C:\Users\jovis\.openclaw\workspace\bookkeepr\app',
    creationflags=subprocess.CREATE_NEW_CONSOLE
)

print(f"Server started: PID {proc.pid}")
time.sleep(5)

session = requests.Session()

# Test login
login_data = {
    'email': 'test@bookkeepr.ai',
    'password': 'password123',
    'remember_me': 'on'
}

response = session.post('http://localhost:5000/auth/login', data=login_data, allow_redirects=True)
print(f"Login: {response.status_code}")
print(f"URL after login: {response.url}")

# Check dashboard
response = session.get('http://localhost:5000/')
print(f"\nDashboard: {response.status_code}")
print(f"Length: {len(response.text)}")

if 'dashboard.css' in response.text:
    print("\n*** NEW BLUE DASHBOARD ACTIVE ***")
    print("CSS link found!")
elif 'BookKeepr AI' in response.text:
    print("\nChecking content...")
    if 'sidebar' in response.text:
        print("Blue sidebar found!")
    else:
        print("Still showing old template")
else:
    print("\nResponse preview:")
    print(response.text[:600])
