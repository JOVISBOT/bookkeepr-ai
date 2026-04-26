"""Diagnose the issue"""
import subprocess
import os

print("DIAGNOSING BOOKKEEPR ISSUE")
print("=" * 50)

# 1. Check if database exists
db_path = r"C:\Users\jovis\.openclaw\workspace\bookkeepr\app\instance\bookkeepr.db"
if os.path.exists(db_path):
    size = os.path.getsize(db_path)
    print(f"✅ Database exists: {size} bytes")
else:
    print("❌ Database NOT found")

# 2. Check Python processes
result = subprocess.run(['tasklist', '/FI', 'IMAGENAME eq python.exe'], capture_output=True, text=True)
python_count = result.stdout.count('python.exe')
print(f"📊 Python processes: {python_count}")

# 3. Check Chrome
result = subprocess.run(['tasklist', '/FI', 'IMAGENAME eq chrome.exe'], capture_output=True, text=True)
chrome_count = result.stdout.count('chrome.exe')
print(f"📊 Chrome processes: {chrome_count}")

# 4. Test server connection
import urllib.request
try:
    response = urllib.request.urlopen('http://localhost:5000/', timeout=3)
    print(f"✅ Server responding: {response.status}")
except Exception as e:
    print(f"❌ Server NOT responding: {e}")

# 5. Check for errors in recent files
log_dir = r"C:\Users\jovis\.openclaw\workspace\bookkeepr"
print(f"\n📁 Recent files in {log_dir}:")
files = sorted(os.listdir(log_dir), key=lambda x: os.path.getmtime(os.path.join(log_dir, x)), reverse=True)[:10]
for f in files:
    if f.endswith(('.txt', '.log', '.err')):
        print(f"  - {f}")

print("\n" + "=" * 50)
print("Diagnosis complete. Check above for issues.")
