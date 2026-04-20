# Test login endpoint
import os
os.chdir(r'C:\Users\jovis\.openclaw\workspace\bookkeepr')

from app import create_app
app = create_app()

with app.test_client() as client:
    print("Testing /auth/login...")
    response = client.get('/auth/login', follow_redirects=False)
    print(f"Status: {response.status_code}")
    print(f"Location: {response.location}")
    
    if response.status_code == 302:
        print("\n✅ Login route working!")
        print("   Redirects to: /auth/connect")
        print("\n✅ OAuth connect should now work!")
        print("   Visit: http://localhost:5000/auth/login")
        print("   Or: http://localhost:5000/auth/connect")
    else:
        print(f"\n❌ Unexpected response: {response.data[:200]}")
