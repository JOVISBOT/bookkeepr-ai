"""Plaid API Client for Bank Integration"""
import os
from plaid.api import plaid_api
from plaid.model.transactions_get_request import TransactionsGetRequest
from plaid.model.accounts_get_request import AccountsGetRequest
from plaid.model.link_token_create_request import LinkTokenCreateRequest
from plaid.model.item_public_token_exchange_request import ItemPublicTokenExchangeRequest
from plaid.configuration import Configuration
from plaid.api_client import ApiClient

class PlaidClient:
    """Plaid client for bank account connectivity"""
    
    def __init__(self):
        self.client_id = os.getenv('PLAID_CLIENT_ID')
        self.secret = os.getenv('PLAID_SECRET')
        self.env = os.getenv('PLAID_ENV', 'sandbox')
        
        configuration = Configuration(
            host=f"https://{self.env}.plaid.com",
            api_key={
                'clientId': self.client_id,
                'secret': self.secret
            }
        )
        api_client = ApiClient(configuration)
        self.client = plaid_api.PlaidApi(api_client)
    
    def create_link_token(self, user_id):
        """Create Plaid Link token for bank connection"""
        request = LinkTokenCreateRequest(
            products=['transactions', 'auth'],
            client_name="BookKeepr",
            country_codes=['US'],
            language='en',
            user={'client_user_id': str(user_id)}
        )
        response = self.client.link_token_create(request)
        return response['link_token']
    
    def exchange_public_token(self, public_token):
        """Exchange public token for access token"""
        request = ItemPublicTokenExchangeRequest(public_token=public_token)
        response = self.client.item_public_token_exchange(request)
        return response['access_token'], response['item_id']
    
    def get_transactions(self, access_token, start_date, end_date):
        """Fetch transactions from connected bank"""
        request = TransactionsGetRequest(
            access_token=access_token,
            start_date=start_date,
            end_date=end_date
        )
        response = self.client.transactions_get(request)
        return response['transactions'], response['accounts']
    
    def get_accounts(self, access_token):
        """Get connected bank accounts"""
        request = AccountsGetRequest(access_token=access_token)
        response = self.client.accounts_get(request)
        return response['accounts']
