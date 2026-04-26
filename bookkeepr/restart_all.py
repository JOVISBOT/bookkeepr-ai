"""Restart everything"""
import subprocess
import time

# Kill everything
print("Stopping existing processes...")
subprocess.run(['taskkill', '/F', '/IM', 'python.exe'], capture_output=True)
subprocess.run(['taskkill', '/F', '/IM', 'chrome.exe'], capture_output=True)
time.sleep(3)

# Start server
print("Starting BookKeepr server...")
subprocess.Popen([
    'python', r'C:\Users\jovis\.openclaw\workspace\bookkeepr\app\run.py'
], creationflags=subprocess.CREATE_NEW_CONSOLE)

time.sleep(8)

# Open Chrome
print("Opening Chrome...")
subprocess.Popen([
    r'C:\Program Files\Google\Chrome\Application\chrome.exe',
    '--new-window',
    'http://localhost:5000/'
])

print("Done! Check your screen for Chrome.")
