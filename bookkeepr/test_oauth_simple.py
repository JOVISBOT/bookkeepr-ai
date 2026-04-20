import os
os.chdir(r'C:\Users\jovis\.openclaw\workspace\bookkeepr')

from dotenv import load_dotenv
load_dotenv()

print("INTUIT_REDIRECT_URI from .env:")
print(repr(os.getenv('INTUIT_REDIRECT_URI')))
print()
print("Client ID:")
print(os.getenv('INTUIT_CLIENT_ID')[:20] + "...")
