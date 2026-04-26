"""Test AI categorization on uncategorized transactions"""
import requests

# Login
session = requests.Session()
session.post('http://localhost:5000/auth/login', data={
    'email': 'test@bookkeepr.ai',
    'password': 'password123'
})

# First, let's reset some transactions to uncategorized
# (This would normally be done via database, but for testing...)

# Test the categorize endpoint
r = session.post('http://localhost:5000/api/v1/ai/categorize')
print('Categorize response:', r.json())
