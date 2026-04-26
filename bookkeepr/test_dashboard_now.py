"""Test if new dashboard is serving"""
import requests

try:
    response = requests.get('http://localhost:5000/', timeout=10)
    print(f"Status: {response.status_code}")
    print(f"Length: {len(response.text)} bytes")
    
    if response.status_code == 200:
        if 'dashboard.css' in response.text:
            print("✅ NEW DASHBOARD SERVING!")
            print("Contains: dashboard.css link")
        elif 'index.html' in response.text or 'React' in response.text:
            print("❌ Still serving old React app")
        else:
            print("Response preview:")
            print(response.text[:800])
    else:
        print(f"Status code: {response.status_code}")
        print(response.text[:500])
        
except Exception as e:
    print(f"❌ Error: {e}")
    print("Server may not be running")
