# Test OAuth URL generation
import os
os.chdir(r'C:\Users\jovis\.openclaw\workspace\bookkeepr')

from dotenv import load_dotenv
load_dotenv()

from app.services.qb_auth import QuickBooksAuthService

auth = QuickBooksAuthService()
url = auth.get_authorization_url(state="test_state_123")

print("Generated OAuth URL:")
print(url)
print()

# Check if state is in URL
if "state=" in url:
    print("OK: State parameter present in URL")
else:
    print("ERROR: State parameter MISSING")
