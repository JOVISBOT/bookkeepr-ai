"""Test AI API"""
import requests

# Login
session = requests.Session()
session.post('http://localhost:5000/auth/login', data={
    'email': 'test@bookkeepr.ai',
    'password': 'password123'
})

# Test AI stats
r = session.get('http://localhost:5000/api/v1/ai/stats')
print('AI Stats:', r.json())

# Test suggestions
r = session.get('http://localhost:5000/api/v1/ai/suggestions')
data = r.json()
print(f"Suggestions: {data['count']} found")
for s in data['suggestions'][:5]:
    print(f"  - {s['description'][:30]} -> {s['suggested_category']} ({s['confidence']*100:.0f}% confidence)")
