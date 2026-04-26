"""QuickBooks Online API Client"""
import os
import requests
from datetime import datetime, timedelta

class QuickBooksClient:
    """QuickBooks Online API client for sync"""
    
    BASE_URL = "https://sandbox-quickbooks.api.intuit.com/v3/company"
    AUTH_URL = "https://oauth.platform.intuit.com/oauth2/v1"
    
    def __init__(self):
        self.client_id = os.getenv('QB_CLIENT_ID')
        self.client_secret = os.getenv('QB_CLIENT_SECRET')
        self.redirect_uri = os.getenv('QB_REDIRECT_URI', 'http://localhost:5000/auth/qb/callback')
        self.realm_id = None
        self.access_token = None
        self.refresh_token = None
    
    def get_auth_url(self, state=None):
        """Generate OAuth authorization URL"""
        scopes = "com.intuit.quickbooks.accounting"
        url = f"https://appcenter.intuit.com/connect/oauth2?"
        url += f"client_id={self.client_id}&"
        url += f"redirect_uri={self.redirect_uri}&"
        url += f"scope={scopes}&"
        url += f"response_type=code"
        if state:
            url += f"&state={state}"
        return url
    
    def exchange_code(self, code, realm_id):
        """Exchange auth code for tokens"""
        self.realm_id = realm_id
        
        response = requests.post(
            f"{self.AUTH_URL}/tokens/bearer",
            headers={
                'Accept': 'application/json',
                'Content-Type': 'application/x-www-form-urlencoded'
            },
            auth=(self.client_id, self.client_secret),
            data={
                'grant_type': 'authorization_code',
                'code': code,
                'redirect_uri': self.redirect_uri
            }
        )
        
        data = response.json()
        self.access_token = data.get('access_token')
        self.refresh_token = data.get('refresh_token')
        
        return {
            'access_token': self.access_token,
            'refresh_token': self.refresh_token,
            'expires_in': data.get('expires_in')
        }
    
    def refresh_access_token(self):
        """Refresh expired access token"""
        response = requests.post(
            f"{self.AUTH_URL}/tokens/bearer",
            headers={'Accept': 'application/json'},
            auth=(self.client_id, self.client_secret),
            data={
                'grant_type': 'refresh_token',
                'refresh_token': self.refresh_token
            }
        )
        
        data = response.json()
        self.access_token = data.get('access_token')
        self.refresh_token = data.get('refresh_token')
        
        return self.access_token
    
    def get_accounts(self):
        """Fetch Chart of Accounts from QBO"""
        url = f"{self.BASE_URL}/{self.realm_id}/query"
        query = "SELECT * FROM Account WHERE Active = true"
        
        response = requests.get(
            url,
            headers={
                'Authorization': f'Bearer {self.access_token}',
                'Accept': 'application/json'
            },
            params={'query': query}
        )
        
        return response.json().get('QueryResponse', {}).get('Account', [])
    
    def create_transaction(self, transaction_data):
        """Create transaction in QBO"""
        url = f"{self.BASE_URL}/{self.realm_id}/purchase"
        
        response = requests.post(
            url,
            headers={
                'Authorization': f'Bearer {self.access_token}',
                'Content-Type': 'application/json',
                'Accept': 'application/json'
            },
            json=transaction_data
        )
        
        return response.json()
    
    def get_transactions(self, start_date=None, end_date=None):
        """Fetch transactions from QBO"""
        if not start_date:
            start_date = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
        if not end_date:
            end_date = datetime.now().strftime('%Y-%m-%d')
        
        url = f"{self.BASE_URL}/{self.realm_id}/query"
        query = f"SELECT * FROM Purchase WHERE TxnDate >= '{start_date}' AND TxnDate <= '{end_date}'"
        
        response = requests.get(
            url,
            headers={
                'Authorization': f'Bearer {self.access_token}',
                'Accept': 'application/json'
            },
            params={'query': query}
        )
        
        return response.json().get('QueryResponse', {}).get('Purchase', [])
