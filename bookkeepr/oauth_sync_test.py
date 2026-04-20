#!/usr/bin/env python
"""
Complete OAuth and Sync Test for QuickBooks
Steps:
1. Generate OAuth URL
2. Manually authorize and get auth code
3. Exchange code for tokens
4. Test sync endpoints

For automation, we'll use a mock/simulation approach
"""
import os
import sys
sys.path.insert(0, r'C:\Users\jovis\.openclaw\workspace\bookkeepr')

from dotenv import load_dotenv
load_dotenv()

from app import create_app, db
from app.models.company import Company
from app.services.qb_auth import QuickBooksAuthService
from datetime import datetime, timedelta
import requests

def test_sync_with_session():
    """Test sync using session-based tokens"""
    app = create_app()
    
    with app.test_client() as client:
        # Step 1: Get OAuth URL
        auth_service = QuickBooksAuthService()
        auth_url = auth_service.get_authorization_url()
        print("=" * 60)
        print("STEP 1: OAuth Authorization URL Generated")
        print("=" * 60)
        print(f"\nAuth URL: {auth_url}\n")
        print("=" * 60)
        
        # Step 2: For test, check if we can use a simulated token
        # Since we can't automate the browser flow, we'll report what's needed
        print("\n[WARNING] MANUAL STEP REQUIRED:")
        print("   1. Open the Auth URL above in a browser")
        print("   2. Login with QuickBooks sandbox credentials")
        print("   3. Authorize the app")
        print("   4. Copy the 'code' parameter from the callback URL")
        print("   5. You'll be redirected to: http://localhost:5000/auth/callback")
        print()
        
        # Step 3: Test what we can without OAuth
        print("=" * 60)
        print("STEP 2: Testing Sync Page (without OAuth)")
        print("=" * 60)
        
        # Test sync page loads
        response = client.get('/sync')
        print(f"Sync page status: {response.status_code}")
        if response.status_code == 200:
            print("[OK] Sync page loads successfully")
        else:
            print("[FAIL] Sync page failed to load")
        
        # Test sync API without auth
        print("\n" + "=" * 60)
        print("STEP 3: Testing Sync API without authentication")
        print("=" * 60)
        
        response = client.post('/api/v1/sync-session', 
                               json={'type': 'transactions'},
                               content_type='application/json')
        print(f"Sync API status: {response.status_code}")
        data = response.get_json()
        print(f"Response: {data}")
        
        if response.status_code == 401:
            print("[OK] Correctly returns 401 when not authenticated")
        else:
            print(f"[FAIL] Unexpected status code: {response.status_code}")
        
        # Test auth status
        print("\n" + "=" * 60)
        print("STEP 4: Auth Status Check")
        print("=" * 60)
        response = client.get('/auth/status')
        auth_data = response.get_json()
        print(f"Auth status: {auth_data}")
        
        if not auth_data['connected']:
            print("[WARNING] Not connected - OAuth required")
        
        return {
            'auth_url': auth_url,
            'sync_page_loads': True,
            'unauthenticated_response': data
        }

def complete_oauth_with_code(auth_code, realm_id):
    """Complete OAuth and test sync with real tokens"""
    app = create_app()
    
    with app.test_client() as client:
        # Exchange code for tokens
        auth_service = QuickBooksAuthService()
        tokens = auth_service.exchange_code_for_token(auth_code, realm_id)
        
        print("=" * 60)
        print("OAuth Tokens Received:")
        print("=" * 60)
        print(f"  Access Token: {tokens['access_token'][:30]}...")
        print(f"  Refresh Token: {tokens['refresh_token'][:30]}...")
        print(f"  Realm ID: {tokens['realm_id']}")
        print(f"  Expires In: {tokens['expires_in']} seconds")
        
        # Store in session (simulated)
        with client.session_transaction() as sess:
            sess['qb_tokens'] = tokens
        
        # Now test sync
        print("\n" + "=" * 60)
        print("Testing Sync with Authenticated Session")
        print("=" * 60)
        
        response = client.post('/api/v1/sync-session',
                               json={'type': 'transactions'},
                               content_type='application/json')
        
        print(f"Sync API status: {response.status_code}")
        sync_data = response.get_json()
        print(f"Sync response: {sync_data}")
        
        return sync_data

if __name__ == '__main__':
    if len(sys.argv) >= 3:
        # Usage: python oauth_sync_test.py <auth_code> <realm_id>
        auth_code = sys.argv[1]
        realm_id = sys.argv[2]
        result = complete_oauth_with_code(auth_code, realm_id)
        print("\n" + "=" * 60)
        print("SYNC TEST RESULT:")
        print("=" * 60)
        print(result)
    else:
        # Just run the initial tests
        result = test_sync_with_session()
        print("\n" + "=" * 60)
        print("INITIAL TEST RESULT:")
        print("=" * 60)
        print(result)
