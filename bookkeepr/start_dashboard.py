"""
Start a simple dashboard to show progress
"""
import subprocess

# Start the quick dashboard
subprocess.Popen([
    'python', r'C:\Users\jovis\.openclaw\workspace\bookkeepr\app\quick_dashboard.py'
], creationflags=subprocess.CREATE_NEW_CONSOLE)

print("Quick dashboard starting on http://localhost:5002")
print("Open your browser to see the live dashboard!")
