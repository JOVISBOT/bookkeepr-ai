"""Check if JavaScript is intercepting navigation"""
import requests

session = requests.Session()

# Login
session.post('http://localhost:5000/auth/login', data={
    'email': 'test@bookkeepr.ai',
    'password': 'password123'
})

# Get dashboard HTML
response = session.get('http://localhost:5000/')
html = response.text

# Check for JavaScript event handlers
import re

# Look for onclick
onclick_links = re.findall(r'onclick="([^"]+)"', html)
print("onclick handlers:", onclick_links)

# Look for javascript:void(0)
void_links = re.findall(r'href="javascript:void\(0\)"', html)
print("javascript:void(0) links:", len(void_links))

# Look for # in href
hash_links = re.findall(r'href="#"', html)
print("hash links:", len(hash_links))

# Look for event listeners
if 'addEventListener' in html:
    print("addEventListener found")
else:
    print("No addEventListener found")

# Check if links have correct URLs
trans_link = re.findall(r'href="(/dashboard/transactions)"', html)
print("Transaction links:", trans_link)
