# Check what redirect URI is being sent
import os
os.chdir(r'C:\Users\jovis\.openclaw\workspace\bookkeepr')

from dotenv import load_dotenv
load_dotenv()

redirect_uri = os.getenv('INTUIT_REDIRECT_URI')
print("Redirect URI from .env file:")
print(f"  '{redirect_uri}'")
print(f"  Length: {len(redirect_uri) if redirect_uri else 0}")
print()
print("Expected format:")
print("  'http://localhost:5000/auth/callback'")
print(f"  Length: 35")
print()
if redirect_uri:
    if redirect_uri == "http://localhost:5000/auth/callback":
        print("✓ Matches exactly!")
    else:
        print("✗ Does NOT match exactly")
        print("  Differences:")
        for i, (a, b) in enumerate(zip(redirect_uri, "http://localhost:5000/auth/callback")):
            if a != b:
                print(f"    Position {i}: got '{a}' expected '{b}'")
