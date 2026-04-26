"""Test billing plans"""
import requests

session = requests.Session()
session.post('http://localhost:5000/auth/login', data={'email': 'test@bookkeepr.ai', 'password': 'password123'})

r = session.get('http://localhost:5000/api/v1/billing/plans')
print('Billing plans:', r.status_code)

if r.status_code == 200:
    plans = r.json()['plans']
    for name, plan in plans.items():
        print(f"\n{plan['name']}: ${plan['price']}/month")
        for f in plan['features']:
            print(f'  - {f}')
