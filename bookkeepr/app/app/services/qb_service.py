"""
QuickBooks Service - Data sync operations
Uses CDC (Change Data Capture) and pagination for efficient syncing
"""
from quickbooks import QuickBooks
from app import db
from app.models.account import Account
from app.models.transaction import Transaction
from app.services.qb_auth import QuickBooksAuthService
from app.services.qb_data_sync import QuickBooksDataSync
from datetime import datetime, timedelta
from typing import Optional, Dict
import logging

logger = logging.getLogger(__name__)


class QuickBooksService:
    """
    Service for QuickBooks data operations
    Handles syncing transactions, accounts, etc.
    
    Uses QuickBooksDataSync for CDC and pagination handling
    """
    
    def __init__(self, company):
        """
        Initialize with company
        
        Args:
            company: Company model with QB credentials
        """
        self.company = company
        self.auth_service = QuickBooksAuthService()
        self.client = None
        self.data_sync = None
        
        # Check if token needs refresh
        if company.needs_token_refresh():
            self._refresh_token()
        
        # Initialize QB client
        if company.access_token and company.qbo_realm_id:
            self.client = QuickBooks(
                consumer_key=self.auth_service.client_id,
                consumer_secret=self.auth_service.client_secret,
                access_token=company.access_token,
                realm_id=company.qbo_realm_id,
                sandbox=self.auth_service.environment == 'sandbox'
            )
            
            # Initialize data sync service
            self.data_sync = QuickBooksDataSync(company, client=self.client)
    
    def _refresh_token(self):
        """Refresh expired access token"""
        if not self.company.refresh_token:
            logger.error("No refresh token available")
            return False
        
        try:
            tokens = self.auth_service.refresh_access_token(self.company.refresh_token)
            self.company.access_token = tokens['access_token']
            self.company.refresh_token = tokens['refresh_token']
            self.company.token_expires_at = datetime.utcnow() + timedelta(seconds=tokens['expires_in'])
            db.session.commit()
            logger.info(f"Token refreshed for company {self.company.id}")
            return True
        except Exception as e:
            logger.error(f"Token refresh failed: {e}")
            self.company.is_connected = False
            db.session.commit()
            return False
    
    def sync_accounts(self) -> Dict:
        """
        Sync chart of accounts from QuickBooks
        
        Uses CDC (Change Data Capture) to only fetch changed records
        on subsequent syncs for efficiency.
        
        Returns:
            dict: {created: int, updated: int, errors: int}
        """
        if not self.data_sync:
            logger.error("Data sync service not initialized")
            return {'created': 0, 'updated': 0, 'errors': 1}
        
        try:
            result = self.data_sync.sync_accounts()
            
            logger.info(f"Synced {result.get('total', 0)} accounts for company {self.company.id}")
            return result
            
        except Exception as e:
            logger.error(f"Account sync failed: {e}")
            return {'created': 0, 'updated': 0, 'errors': 1}
    
    def sync_transactions(self, start_date: Optional[datetime] = None, 
                         end_date: Optional[datetime] = None) -> Dict:
        """
        Sync transactions from QuickBooks
        
        Fetches transactions using CDC (Change Data Capture) approach:
        - First sync: Full data for date range
        - Subsequent syncs: Only records changed since last sync
        
        Handles:
        - Purchases (expenses, bills)
        - Deposits (income)
        - Journal Entries
        - Payments
        
        Args:
            start_date: Optional start date filter (default: 90 days ago)
            end_date: Optional end date filter (default: today)
            
        Returns:
            dict: {count: int, updated: int, errors: int, skipped: int}
        """
        if not self.data_sync:
            logger.error("Data sync service not initialized")
            return {'count': 0, 'updated': 0, 'errors': 1, 'skipped': 0}
        
        # Default to last 90 days if no dates provided
        if not end_date:
            end_date = datetime.utcnow()
        if not start_date:
            start_date = end_date - timedelta(days=90)
        
        try:
            result = self.data_sync.sync_transactions(start_date, end_date)
            
            # Update company sync status on success
            total_synced = result.get('created', 0) + result.get('updated', 0)
            if result.get('errors', 0) == 0:
                self.company.update_sync_status('success')
            else:
                self.company.update_sync_status('partial', f"{result.get('errors')} errors occurred")
            
            db.session.commit()
            
            logger.info(f"Synced {total_synced} transactions for company {self.company.id}")
            
            return {
                'count': result.get('created', 0),
                'updated': result.get('updated', 0),
                'errors': result.get('errors', 0),
                'skipped': result.get('skipped', 0)
            }
            
        except Exception as e:
            logger.error(f"Transaction sync failed: {e}")
            self.company.update_sync_status('error', str(e))
            db.session.commit()
            return {'count': 0, 'updated': 0, 'errors': 1, 'skipped': 0}
    
    def sync_all(self, start_date: Optional[datetime] = None,
                 end_date: Optional[datetime] = None) -> Dict:
        """
        Perform full sync of accounts and transactions
        
        Args:
            start_date: Optional start date
            end_date: Optional end date
            
        Returns:
            Dict with sync results
        """
        if not self.data_sync:
            logger.error("Data sync service not initialized")
            return {
                'success': False,
                'error': 'Data sync service not initialized',
                'accounts': {'created': 0, 'updated': 0, 'errors': 1},
                'transactions': {'created': 0, 'updated': 0, 'errors': 1}
            }
        
        logger.info(f"Starting full sync for company {self.company.id}")
        
        return self.data_sync.sync_all(start_date, end_date)
    
    def get_company_info(self) -> Optional[Dict]:
        """
        Get company info from QuickBooks
        
        Returns:
            dict: Company info
        """
        if not self.client:
            return None
        
        try:
            company_info = self.client.get_company_info()
            return {
                'company_name': company_info.CompanyName,
                'legal_name': getattr(company_info, 'LegalName', None),
                'country': getattr(company_info, 'Country', 'US'),
                'fiscal_year_start_month': getattr(company_info, 'FiscalYearStartMonth', 1)
            }
        except Exception as e:
            logger.error(f"Failed to get company info: {e}")
            return None
    
    def get_account_balance(self, qb_account_id: str) -> Optional[float]:
        """
        Get current balance for an account
        
        Args:
            qb_account_id: QB account ID
            
        Returns:
            Current balance or None
        """
        if not self.client:
            return None
        
        try:
            from quickbooks.objects import Account as QBAccount
            account = QBAccount.get(qb_account_id, qb=self.client)
            return getattr(account, 'CurrentBalance', 0)
        except Exception as e:
            logger.error(f"Failed to get account balance: {e}")
            return None
    
    def validate_connection(self) -> bool:
        """
        Validate QuickBooks connection is working
        
        Returns:
            True if connection is valid
        """
        if not self.client:
            return False
        
        try:
            # Try to get company info as validation
            self.get_company_info()
            return True
        except Exception as e:
            logger.error(f"Connection validation failed: {e}")
            return False