"""Check what HTML Chrome is getting"""
import requests

# Test with session
session = requests.Session()

# Login
session.post('http://localhost:5000/auth/login', data={
    'email': 'test@bookkeepr.ai',
    'password': 'password123'
})

# Get main page
response = session.get('http://localhost:5000/')
html = response.text

# Check what links are in the HTML
import re
links = re.findall(r'href="([^"]+)"[^>]*class="nav-item"', html)
print("Nav links found:")
for link in links:
    print(f"  {link}")

# Check if it's using the right template
if 'dashboard.css' in html:
    print("\nNew dashboard template (dashboard.css found)")
elif 'tailwindcss' in html:
    print("\nOld template (tailwindcss found)")
else:
    print("\nUnknown template")
