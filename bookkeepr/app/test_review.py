import os, sys
from dotenv import load_dotenv
load_dotenv()
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from app import create_app
app = create_app()

with app.test_client() as client:
    client.post('/auth/login', data={'email': 'test@bookkeepr.ai', 'password': 'TestPass123!'})
    
    r = client.get('/review/')
    print(f'/review/: {r.status_code} ({len(r.data)} bytes)')
    
    r = client.get('/api/v1/ai/categorize')
    print(f'GET /api/v1/ai/categorize: {r.status_code}')
    
    r = client.post('/api/v1/ai/categorize')
    print(f'POST /api/v1/ai/categorize: {r.status_code}')
    print(f'  body: {r.data[:300].decode()}')
    
    # Also try the dashboard run-categorization endpoint
    for path in ['/dashboard/ai/run-categorization', '/api/v1/ai/run', '/api/v1/ai/categorize-batch']:
        r = client.post(path)
        print(f'POST {path}: {r.status_code}')
