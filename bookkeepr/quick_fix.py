"""Quick fix for server"""
import subprocess
import time

# Kill existing Python processes
subprocess.run(['taskkill', '/F', '/IM', 'python.exe'], capture_output=True)
time.sleep(2)

# Start server
print("Starting server...")
subprocess.Popen([
    'python', r'C:\Users\jovis\.openclaw\workspace\bookkeepr\app\run.py'
], creationflags=subprocess.CREATE_NEW_CONSOLE)

time.sleep(5)
print("Server should be running on localhost:5000")
