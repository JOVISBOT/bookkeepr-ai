"""Check what screenshots exist"""
import os

dir_path = r"C:\Users\jovis\.openclaw\workspace\bookkeepr"
files = os.listdir(dir_path)

screenshots = [f for f in files if f.endswith('.png') and 'progress' in f.lower()]
print("Screenshots found:")
for s in screenshots:
    full_path = os.path.join(dir_path, s)
    size = os.path.getsize(full_path)
    print(f"  {s} ({size} bytes)")

if not screenshots:
    print("No screenshots found. Server might not be running.")
    print("\nChecking server status...")
    import subprocess
    result = subprocess.run(['curl', '-s', '-o', 'nul', '-w', '%{http_code}', 'http://localhost:5000/'], 
                          capture_output=True, text=True, shell=True)
    print(f"Server response: {result.stdout}")
