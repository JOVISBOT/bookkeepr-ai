# Debug OAuth URL generation
import os
os.chdir(r'C:\Users\jovis\.openclaw\workspace\bookkeepr')

from dotenv import load_dotenv
load_dotenv()

from intuitlib.client import AuthClient
from intuitlib.enums import Scopes
import urllib.parse

# Create auth client
auth_client = AuthClient(
    client_id=os.getenv('INTUIT_CLIENT_ID'),
    client_secret=os.getenv('INTUIT_CLIENT_SECRET'),
    environment='sandbox',
    redirect_uri='http://localhost:5000/auth/callback'
)

# Get scopes
scopes = [Scopes.ACCOUNTING, Scopes.OPENID, Scopes.PROFILE, Scopes.EMAIL]

# Generate auth URL
auth_url = auth_client.get_authorization_url(scopes)

print("Full Auth URL being sent to Intuit:")
print(auth_url)
print()

# Parse the URL to see redirect_uri parameter
parsed = urllib.parse.urlparse(auth_url)
params = urllib.parse.parse_qs(parsed.query)

print("Parameters in URL:")
for key, value in params.items():
    print(f"  {key}: {value[0]}")

print()
print("redirect_uri value (URL decoded):")
redirect_uri = params.get('redirect_uri', [''])[0]
print(urllib.parse.unquote(redirect_uri))
print()

# Compare with what we expect
expected = "http://localhost:5000/auth/callback"
if urllib.parse.unquote(redirect_uri) == expected:
    print("✅ redirect_uri matches expected value")
else:
    print("❌ redirect_uri DOES NOT match!")
    print(f"   Expected: {expected}")
    print(f"   Got: {urllib.parse.unquote(redirect_uri)}")
