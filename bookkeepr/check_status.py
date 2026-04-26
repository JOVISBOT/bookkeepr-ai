"""Quick status check"""
import subprocess
import os

# Check server
result = subprocess.run(['curl', '-s', '-o', 'nul', '-w', '%{http_code}', 'http://localhost:5000/'], 
                       capture_output=True, text=True, shell=True)
print(f"Server status: {result.stdout.strip()}")

# Check database
db = r"C:\Users\jovis\.openclaw\workspace\bookkeepr\app\instance\bookkeepr.db"
print(f"Database exists: {os.path.exists(db)}")
