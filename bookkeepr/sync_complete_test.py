# QuickBooks OAuth and Sync Test Script
# Usage: python sync_complete_test.py <auth_code> <realm_id>
#
# To get auth_code and realm_id:
# 1. Visit: https://appcenter.intuit.com/connect/oauth2?client_id=ABybcYSxG6VYvQcHPKIJyinQN5gS93kTBgYtFSW0545tzM2S5e&response_type=code&scope=com.intuit.quickbooks.accounting%20openid%20profile%20email&redirect_uri=http%3A%2F%2Flocalhost%3A5000%2Fauth%2Fcallback&state=test123
# 2. Login with sandbox credentials:
#    - Username: jovis@bookkeepr.ai
#    - Password: (check .env or Intuit developer account)
# 3. Authorize the app
# 4. Copy the 'code' and 'realmId' from the callback URL

import sys
sys.path.insert(0, r'C:\Users\jovis\.openclaw\workspace\bookkeepr')

from dotenv import load_dotenv
load_dotenv()

from app import create_app, db
from app.models.company import Company
from app.models.transaction import Transaction
from app.services.qb_auth import QuickBooksAuthService
from app.services.qb_service import QuickBooksService
from datetime import datetime, timedelta

def complete_oauth_and_sync(auth_code, realm_id):
    """Complete OAuth and run sync test"""
    print("=" * 70)
    print("QUICKBOOKS SYNC TEST - COMPLETE WORKFLOW")
    print("=" * 70)
    
    app = create_app()
    
    with app.app_context():
        # Step 1: Exchange auth code for tokens
        print("\n[STEP 1] Exchanging auth code for tokens...")
        auth_service = QuickBooksAuthService()
        
        try:
            tokens = auth_service.exchange_code_for_token(auth_code, realm_id)
            print(f"  [OK] Tokens received!")
            print(f"       Access Token: {tokens['access_token'][:40]}...")
            print(f"       Refresh Token: {tokens['refresh_token'][:40]}...")
            print(f"       Realm ID: {tokens['realm_id']}")
            print(f"       Expires In: {tokens['expires_in']} seconds")
        except Exception as e:
            print(f"  [FAIL] Token exchange failed: {e}")
            return {'success': False, 'error': str(e), 'step': 'token_exchange'}
        
        # Step 2: Create/Update company in database
        print("\n[STEP 2] Setting up company in database...")
        company = Company.query.filter_by(realm_id=realm_id).first()
        
        if not company:
            company = Company(
                name=f"Sandbox Company {realm_id}",
                realm_id=realm_id,
                access_token=tokens['access_token'],
                refresh_token=tokens['refresh_token'],
                token_expires_at=datetime.utcnow() + timedelta(seconds=tokens['expires_in']),
                is_qbo=True,
                is_connected=True
            )
            db.session.add(company)
            db.session.commit()
            print(f"  [OK] Created new company (ID: {company.id})")
        else:
            company.access_token = tokens['access_token']
            company.refresh_token = tokens['refresh_token']
            company.token_expires_at = datetime.utcnow() + timedelta(seconds=tokens['expires_in'])
            company.is_connected = True
            db.session.commit()
            print(f"  [OK] Updated existing company (ID: {company.id})")
        
        # Step 3: Test connection
        print("\n[STEP 3] Testing QuickBooks connection...")
        try:
            qb_service = QuickBooksService(company)
            company_info = qb_service.get_company_info()
            if company_info:
                print(f"  [OK] Connected to: {company_info.get('company_name', 'Unknown')}")
                company.name = company_info.get('company_name', company.name)
                db.session.commit()
            else:
                print(f"  [WARNING] Could not retrieve company info")
        except Exception as e:
            print(f"  [FAIL] Connection test failed: {e}")
            return {'success': False, 'error': str(e), 'step': 'connection_test'}
        
        # Step 4: Sync Accounts
        print("\n[STEP 4] Syncing Chart of Accounts...")
        try:
            result = qb_service.sync_accounts()
            print(f"  [OK] Accounts synced!")
            print(f"       Created: {result.get('created', 0)}")
            print(f"       Updated: {result.get('updated', 0)}")
            print(f"       Errors: {result.get('errors', 0)}")
            accounts_result = result
        except Exception as e:
            print(f"  [FAIL] Account sync failed: {e}")
            accounts_result = {'created': 0, 'updated': 0, 'errors': 1, 'error': str(e)}
        
        # Step 5: Sync Transactions (last 90 days)
        print("\n[STEP 5] Syncing Transactions...")
        try:
            end_date = datetime.utcnow()
            start_date = end_date - timedelta(days=90)
            result = qb_service.sync_transactions(start_date=start_date, end_date=end_date)
            print(f"  [OK] Transactions synced!")
            print(f"       Created: {result.get('count', 0)}")
            print(f"       Updated: {result.get('updated', 0)}")
            print(f"       Skipped: {result.get('skipped', 0)}")
            print(f"       Errors: {result.get('errors', 0)}")
            transactions_result = result
        except Exception as e:
            print(f"  [FAIL] Transaction sync failed: {e}")
            transactions_result = {'count': 0, 'updated': 0, 'skipped': 0, 'errors': 1, 'error': str(e)}
        
        # Step 6: Verify database entries
        print("\n[STEP 6] Verifying database entries...")
        
        from app.models.account import Account
        account_count = Account.query.filter_by(company_id=company.id).count()
        txn_count = Transaction.query.filter_by(company_id=company.id).count()
        
        print(f"  Accounts in database: {account_count}")
        print(f"  Transactions in database: {txn_count}")
        
        # Step 7: Show sample data
        print("\n[STEP 7] Sample synced data...")
        if account_count > 0:
            sample_accounts = Account.query.filter_by(company_id=company.id).limit(5).all()
            print(f"  Sample Accounts:")
            for acc in sample_accounts:
                print(f"    - {acc.name} ({acc.account_type})")
        
        if txn_count > 0:
            sample_txns = Transaction.query.filter_by(company_id=company.id).order_by(
                Transaction.transaction_date.desc()).limit(5).all()
            print(f"  Sample Transactions:")
            for txn in sample_txns:
                print(f"    - {txn.transaction_date}: {txn.description or 'N/A'} - ${txn.amount}")
        
        # Final Summary
        print("\n" + "=" * 70)
        print("SYNC TEST SUMMARY")
        print("=" * 70)
        
        success = (accounts_result.get('errors', 0) == 0 and 
                   transactions_result.get('errors', 0) == 0)
        
        summary = {
            'success': success,
            'company_id': company.id,
            'company_name': company.name,
            'accounts_synced': accounts_result.get('created', 0) + accounts_result.get('updated', 0),
            'transactions_synced': transactions_result.get('count', 0) + transactions_result.get('updated', 0),
            'accounts_in_db': account_count,
            'transactions_in_db': txn_count,
            'errors': accounts_result.get('errors', 0) + transactions_result.get('errors', 0)
        }
        
        print(f"  Status: {'SUCCESS' if success else 'PARTIAL/FAILURE'}")
        print(f"  Company: {summary['company_name']} (ID: {summary['company_id']})")
        print(f"  Accounts Synced: {summary['accounts_synced']}")
        print(f"  Transactions Synced: {summary['transactions_synced']}")
        print(f"  Total Errors: {summary['errors']}")
        
        return summary

if __name__ == '__main__':
    if len(sys.argv) < 3:
        print("Usage: python sync_complete_test.py <auth_code> <realm_id>")
        print()
        print("To get auth_code and realm_id:")
        print("1. Visit the OAuth URL in a browser")
        print("2. Login and authorize the app")
        print("3. Copy 'code' and 'realmId' from the callback URL")
        print()
        # Generate fresh auth URL
        from app.services.qb_auth import QuickBooksAuthService
        auth_service = QuickBooksAuthService()
        auth_url = auth_service.get_authorization_url()
        print(f"\nOAuth URL:\n{auth_url}")
    else:
        auth_code = sys.argv[1]
        realm_id = sys.argv[2]
        result = complete_oauth_and_sync(auth_code, realm_id)
        print("\n" + "=" * 70)
        print("FINAL RESULT:")
        print(result)
