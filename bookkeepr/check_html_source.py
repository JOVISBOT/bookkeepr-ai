"""Check if charts are in HTML"""
import requests

session = requests.Session()
session.post('http://localhost:5000/auth/login', data={
    'email': 'test@bookkeepr.ai',
    'password': 'password123'
})

response = session.get('http://localhost:5000/')
html = response.text

# Check for chart elements
if 'pnlChart' in html:
    print("pnlChart found in HTML")
else:
    print("pnlChart NOT found in HTML")

if 'expenseChart' in html:
    print("expenseChart found in HTML")
else:
    print("expenseChart NOT found in HTML")

if 'chart.js' in html.lower():
    print("Chart.js found in HTML")
else:
    print("Chart.js NOT found in HTML")

if 'Financial Overview' in html:
    print("Financial Overview section found")
else:
    print("Financial Overview section NOT found")
