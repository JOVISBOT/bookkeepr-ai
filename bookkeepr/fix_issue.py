"""Fix the issue"""
import subprocess
import time

# Check what's running
result = subprocess.run(['tasklist'], capture_output=True, text=True)
print("Running processes:")
if 'python.exe' in result.stdout:
    print("- Python is running")
if 'chrome.exe' in result.stdout:
    print("- Chrome is running")

# Start server if not running
print("\nStarting BookKeepr server...")
subprocess.Popen([
    'python', r'C:\Users\jovis\.openclaw\workspace\bookkeepr\app\run.py'
], creationflags=subprocess.CREATE_NEW_CONSOLE)

time.sleep(5)

# Check if server started
import urllib.request
try:
    response = urllib.request.urlopen('http://localhost:5000/', timeout=5)
    print(f"Server started: {response.status}")
except Exception as e:
    print(f"Server failed: {e}")
