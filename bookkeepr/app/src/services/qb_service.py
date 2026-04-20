"""
QuickBooks integration service
Handles OAuth, API calls, and data synchronization
"""
import requests
from datetime import datetime, timedelta
from flask import current_app, url_for
from intuitlib.client import AuthClient
from intuitlib.exceptions import AuthClientError

from ..extensions import db
from ..models import Company, Transaction, Category


class QuickBooksService:
    """Service class for QuickBooks Online integration."""
    
    SCOPES = ['com.intuit.quickbooks.accounting']
    
    def __init__(self, company=None):
        """
        Initialize QBO service.
        
        Args:
            company: Company model instance (optional)
        """
        self.company = company
        self.auth_client = None
        
        if company:
            self._init_auth_client()
    
    def _init_auth_client(self):
        """Initialize Intuit OAuth client."""
        self.auth_client = AuthClient(
            client_id=current_app.config['QBO_CLIENT_ID'],
            client_secret=current_app.config['QBO_CLIENT_SECRET'],
            environment='sandbox' if current_app.config['QBO_SANDBOX_MODE'] else 'production',
            redirect_uri=url_for('auth.qbo_callback', _external=True)
        )
    
    def get_authorization_url(self, state=None):
        """
        Generate OAuth authorization URL.
        
        Returns:
            str: Authorization URL to redirect user
        """
        if not self.auth_client:
            self._init_auth_client()
        
        auth_url = self.auth_client.get_authorization_url(self.SCOPES)
        return auth_url
    
    def exchange_code_for_tokens(self, auth_code, realm_id):
        """
        Exchange OAuth authorization code for access/refresh tokens.
        
        Args:
            auth_code: Authorization code from OAuth callback
            realm_id: QuickBooks company realm ID
            
        Returns:
            dict: Token data or None if error
        """
        try:
            if not self.auth_client:
                self._init_auth_client()
            
            self.auth_client.get_bearer_token(auth_code, realm_id=realm_id)
            
            return {
                'access_token': self.auth_client.access_token,
                'refresh_token': self.auth_client.refresh_token,
                'expires_in': self.auth_client.expires_in,
                'realm_id': realm_id
            }
        except AuthClientError as e:
            current_app.logger.error(f"OAuth token exchange failed: {e}")
            return None
    
    def refresh_access_token(self):
        """
        Refresh expired access token.
        
        Returns:
            bool: True if successful
        """
        if not self.company or not self.company.refresh_token:
            return False
        
        try:
            if not self.auth_client:
                self._init_auth_client()
            
            self.auth_client.refresh_token = self.company.refresh_token
            self.auth_client.refresh()
            
            # Update company tokens
            self.company.update_tokens(
                access_token=self.auth_client.access_token,
                refresh_token=self.auth_client.refresh_token,
                expires_in=self.auth_client.expires_in
            )
            db.session.commit()
            
            return True
        except AuthClientError as e:
            current_app.logger.error(f"Token refresh failed: {e}")
            self.company.mark_error(str(e))
            db.session.commit()
            return False
    
    def _get_headers(self):
        """Get authorization headers for API requests."""
        if not self.company:
            raise ValueError("No company set")
        
        # Check if token needs refresh
        if self.company.is_token_expired:
            if not self.refresh_access_token():
                raise Exception("Failed to refresh access token")
        
        return {
            'Authorization': f'Bearer {self.company.access_token}',
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        }
    
    def _make_request(self, endpoint, method='GET', data=None, params=None):
        """
        Make authenticated request to QBO API.
        
        Args:
            endpoint: API endpoint path
            method: HTTP method
            data: Request body (for POST/PUT)
            params: Query parameters
            
        Returns:
            dict: Response JSON or None
        """
        if not self.company:
            raise ValueError("No company set")
        
        base_url = current_app.config['QBO_BASE_URL']
        url = f"{base_url}/v3/company/{self.company.realm_id}/{endpoint}"
        
        headers = self._get_headers()
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=headers, params=params, timeout=30)
            elif method == 'POST':
                response = requests.post(url, headers=headers, json=data, timeout=30)
            elif method == 'PUT':
                response = requests.put(url, headers=headers, json=data, timeout=30)
            else:
                raise ValueError(f"Unsupported method: {method}")
            
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.RequestException as e:
            current_app.logger.error(f"QBO API request failed: {e}")
            return None
    
    def get_company_info(self):
        """Get company information from QBO."""
        return self._make_request('companyinfo/' + self.company.realm_id)
    
    def get_chart_of_accounts(self):
        """Get chart of accounts."""
        return self._make_request('query', params={
            'query': 'SELECT * FROM Account WHERE Active = true'
        })
    
    def get_transactions(self, start_date=None, end_date=None, limit=100):
        """
        Get transactions from QBO.
        
        Args:
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
            limit: Max results
            
        Returns:
            list: Transaction data
        """
        # Build query
        query = "SELECT * FROM Purchase WHERE TxnStatus != 'Deleted'"
        
        if start_date:
            query += f" AND TxnDate >= '{start_date}'"
        if end_date:
            query += f" AND TxnDate <= '{end_date}'"
        
        query += f" ORDER BY TxnDate DESC MAXRESULTS {limit}"
        
        result = self._make_request('query', params={'query': query})
        
        if result and 'QueryResponse' in result:
            return result['QueryResponse'].get('Purchase', [])
        return []
    
    def import_transactions(self, start_date=None, end_date=None):
        """
        Import transactions from QBO into local database.
        
        Args:
            start_date: Start date
            end_date: End date
            
        Returns:
            dict: Import stats
        """
        if not self.company:
            raise ValueError("No company set")
        
        imported_count = 0
        skipped_count = 0
        
        try:
            transactions = self.get_transactions(start_date, end_date)
            
            for tx_data in transactions:
                qbo_id = str(tx_data.get('Id'))
                
                # Check if already exists
                existing = Transaction.query.filter_by(
                    company_id=self.company.id,
                    qbo_id=qbo_id
                ).first()
                
                if existing:
                    skipped_count += 1
                    continue
                
                # Parse transaction data
                txn_date = datetime.strptime(tx_data.get('TxnDate'), '%Y-%m-%d').date()
                total_amount = tx_data.get('TotalAmt', 0)
                
                # Get vendor
                vendor = ''
                if 'EntityRef' in tx_data:
                    vendor = tx_data['EntityRef'].get('name', '')
                
                # Get account
                account_name = ''
                account_id = ''
                if 'AccountRef' in tx_data:
                    account_name = tx_data['AccountRef'].get('name', '')
                    account_id = tx_data['AccountRef'].get('value', '')
                
                # Create transaction
                transaction = Transaction(
                    company_id=self.company.id,
                    qbo_id=qbo_id,
                    qbo_transaction_type=tx_data.get('PaymentType', 'Cash'),
                    date=txn_date,
                    amount=total_amount,
                    description=tx_data.get('PrivateNote', ''),
                    memo=tx_data.get('Memo', ''),
                    vendor=vendor,
                    account_id=account_id,
                    account_name=account_name,
                    transaction_type='expense',
                    status='imported',
                    source='qbo'
                )
                
                db.session.add(transaction)
                imported_count += 1
            
            # Update last sync
            self.company.mark_synced()
            db.session.commit()
            
            return {
                'imported': imported_count,
                'skipped': skipped_count,
                'total': imported_count + skipped_count,
                'success': True
            }
            
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Transaction import failed: {e}")
            return {
                'imported': imported_count,
                'skipped': skipped_count,
                'error': str(e),
                'success': False
            }
    
    @staticmethod
    def create_default_categories(company_id):
        """
        Create default categories for a company.
        
        Args:
            company_id: Company ID
        """
        defaults = Category.get_default_categories()
        
        for cat_data in defaults:
            existing = Category.query.filter_by(
                company_id=company_id,
                name=cat_data['name']
            ).first()
            
            if not existing:
                category = Category(
                    company_id=company_id,
                    name=cat_data['name'],
                    account_type=cat_data['account_type'],
                    is_default=True,
                    is_active=True
                )
                db.session.add(category)
        
        db.session.commit()
