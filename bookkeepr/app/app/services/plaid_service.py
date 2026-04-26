"""
Plaid Bank Feed Integration Service
Connects to 12,000+ banks for automatic transaction import
"""
import os
from datetime import datetime, timedelta
import plaid
from plaid.api import plaid_api
from plaid.model.transactions_get_request import TransactionsGetRequest
from plaid.model.transactions_get_request_options import TransactionsGetRequestOptions
from plaid.model.accounts_get_request import AccountsGetRequest
from plaid.model.item_public_token_exchange_request import ItemPublicTokenExchangeRequest
from plaid.model.link_token_create_request import LinkTokenCreateRequest
from plaid.model.link_token_create_request_user import LinkTokenCreateRequestUser
from plaid.model.country_code import CountryCode
from plaid.model.products import Products

class PlaidService:
    """Handle all Plaid operations"""
    
    def __init__(self):
        self.client_id = os.environ.get('PLAID_CLIENT_ID')
        self.secret = os.environ.get('PLAID_SECRET')
        self.environment = os.environ.get('PLAID_ENV', 'sandbox')
        
        configuration = plaid.Configuration(
            host=self._get_host(),
            api_key={
                'clientId': self.client_id,
                'secret': self.secret,
                'plaidVersion': '2020-09-14'
            }
        )
        api_client = plaid.ApiClient(configuration)
        self.client = plaid_api.PlaidApi(api_client)
    
    def _get_host(self):
        """Get Plaid API host based on environment"""
        if self.environment == 'production':
            return plaid.Environment.Production
        elif self.environment == 'development':
            return plaid.Environment.Development
        return plaid.Environment.Sandbox
    
    def create_link_token(self, user_id, client_name="BookKeepr AI"):
        """Create Plaid Link token for frontend"""
        try:
            request = LinkTokenCreateRequest(
                products=[Products('transactions')],
                client_name=client_name,
                country_codes=[CountryCode('US')],
                language='en',
                user=LinkTokenCreateRequestUser(client_user_id=str(user_id)),
                redirect_uri='http://localhost:5000/api/v1/banks/callback'
            )
            response = self.client.link_token_create(request)
            return {
                'success': True,
                'link_token': response['link_token'],
                'expiration': response['expiration']
            }
        except plaid.ApiException as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def exchange_public_token(self, public_token):
        """Exchange public token for access token"""
        try:
            request = ItemPublicTokenExchangeRequest(
                public_token=public_token
            )
            response = self.client.item_public_token_exchange(request)
            return {
                'success': True,
                'access_token': response['access_token'],
                'item_id': response['item_id']
            }
        except plaid.ApiException as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_accounts(self, access_token):
        """Get bank accounts"""
        try:
            request = AccountsGetRequest(access_token=access_token)
            response = self.client.accounts_get(request)
            return {
                'success': True,
                'accounts': response['accounts'],
                'item': response['item']
            }
        except plaid.ApiException as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_transactions(self, access_token, start_date=None, end_date=None, account_ids=None):
        """Get transactions from bank"""
        try:
            if not start_date:
                start_date = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
            if not end_date:
                end_date = datetime.now().strftime('%Y-%m-%d')
            
            request = TransactionsGetRequest(
                access_token=access_token,
                start_date=start_date,
                end_date=end_date,
                options=TransactionsGetRequestOptions(account_ids=account_ids) if account_ids else None
            )
            response = self.client.transactions_get(request)
            
            return {
                'success': True,
                'transactions': response['transactions'],
                'total_transactions': response['total_transactions'],
                'accounts': response['accounts']
            }
        except plaid.ApiException as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def sync_transactions(self, access_token, cursor=None):
        """Sync new transactions (incremental)"""
        try:
            from plaid.model.transactions_sync_request import TransactionsSyncRequest
            
            request = TransactionsSyncRequest(
                access_token=access_token,
                cursor=cursor
            )
            response = self.client.transactions_sync(request)
            
            return {
                'success': True,
                'added': response['added'],
                'modified': response['modified'],
                'removed': response['removed'],
                'next_cursor': response['next_cursor'],
                'has_more': response['has_more']
            }
        except plaid.ApiException as e:
            return {
                'success': False,
                'error': str(e)
            }

# Create service instance
plaid_service = PlaidService()
