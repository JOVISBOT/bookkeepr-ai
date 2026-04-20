# Quick test to verify credentials
import os
from dotenv import load_dotenv

os.chdir(r'C:\Users\jovis\.openclaw\workspace\bookkeepr')
load_dotenv()

client_id = os.getenv('INTUIT_CLIENT_ID')
client_secret = os.getenv('INTUIT_CLIENT_SECRET')
redirect_uri = os.getenv('INTUIT_REDIRECT_URI')

print("Environment loaded")
print(f"Client ID: {client_id[:10]}..." if client_id else "Missing")
print(f"Client Secret: {'Set' if client_secret else 'Missing'}")
print(f"Redirect URI: {redirect_uri}")

# Test importing Flask app
try:
    from app import create_app
    print("\nFlask app imports successfully")
    app = create_app()
    print("Flask app created")
    print("\nReady to start!")
except Exception as e:
    print(f"\nError: {e}")
