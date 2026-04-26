"""Test all BookKeepr functionality"""
import requests

session = requests.Session()
session.post('http://localhost:5000/auth/login', data={'email': 'test@bookkeepr.ai', 'password': 'password123'})

endpoints = [
    ('/', 'Dashboard'),
    ('/dashboard/transactions', 'Transactions'),
    ('/dashboard/accounts', 'Accounts'),
    ('/dashboard/reports', 'Reports'),
    ('/dashboard/settings', 'Settings'),
    ('/api/v1/ai/stats', 'AI Stats'),
    ('/api/v1/ai/suggestions', 'AI Suggestions'),
    ('/api/v1/data/pnl', 'Chart P&L'),
    ('/api/v1/data/balance', 'Chart Balance'),
    ('/api/v1/data/expenses', 'Chart Expenses'),
    ('/api/v1/reports/pnl', 'Report P&L CSV'),
    ('/api/v1/reports/balance', 'Report Balance CSV'),
    ('/api/v1/billing/plans', 'Billing Plans'),
    ('/api/v1/banks/connect', 'Bank Connect'),
]

print('FUNCTIONAL TEST RESULTS:')
print('=' * 60)
all_pass = True
for endpoint, name in endpoints:
    r = session.get(f'http://localhost:5000{endpoint}')
    status = 'PASS' if r.status_code == 200 else 'FAIL'
    if status == 'FAIL':
        all_pass = False
    print(f'{status}: {name} ({r.status_code})')

print('=' * 60)
overall = 'ALL FUNCTIONAL' if all_pass else 'SOME ISSUES'
print(f'OVERALL: {overall}')
