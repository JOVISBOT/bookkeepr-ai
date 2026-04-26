"""
QuickBooks Data Sync - CDC (Change Data Capture) and pagination handling
"""
from quickbooks import QuickBooks
from quickbooks.objects import Account as QBAccount
from quickbooks.objects import Purchase, Deposit, JournalEntry, Payment
from intuitlib.exceptions import AuthClientError
from app import db
from app.models.account import Account
from app.models.transaction import Transaction
from app.services.qb_auth import (
    QuickBooksAuthService, 
    ensure_valid_token, 
    with_auto_refresh,
    refresh_company_token,
    TokenRefreshError
)
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
import logging
import json

logger = logging.getLogger(__name__)


class QuickBooksDataSync:
    """
    Handles syncing data from QuickBooks using CDC and pagination
    """
    
    # CDC entity types supported by QuickBooks API
    ENTITY_TYPES = ['Account', 'Purchase', 'Deposit', 'JournalEntry', 'Payment']
    
    # Batch sizes for pagination
    PAGE_SIZE = 100
    MAX_PAGES = 100  # Safety limit
    
    def __init__(self, company, client=None):
        """
        Initialize with company and optional QB client
        
        Args:
            company: Company model with QB credentials
            client: Optional QuickBooks client (will be created if not provided)
        """
        self.company = company
        self.client = client
        self.sync_stats = {
            'accounts': {'created': 0, 'updated': 0, 'errors': 0},
            'transactions': {'created': 0, 'updated': 0, 'errors': 0, 'skipped': 0}
        }
        self._auth_service = None
        
        if not self.client and company.access_token and company.qbo_realm_id:
            self._initialize_client()
    
    def _get_auth_service(self):
        """Get or create auth service"""
        if not self._auth_service:
            self._auth_service = QuickBooksAuthService()
        return self._auth_service
    
    def _initialize_client(self):
        """Initialize or reinitialize the QB client with current tokens"""
        auth_service = self._get_auth_service()
        self.client = QuickBooks(
            consumer_key=auth_service.client_id,
            consumer_secret=auth_service.client_secret,
            access_token=self.company.access_token,
            realm_id=self.company.qbo_realm_id,
            sandbox=auth_service.environment == 'sandbox'
        )
        logger.debug(f"QB client initialized for company {self.company.id}")

    @with_auto_refresh('company')
    def _ensure_token_valid(self):
        """
        Check and refresh token if needed before API call.
        
        This method is decorated with @with_auto_refresh which automatically
        handles token refresh if needed. Additionally, reinitializes the
        QB client with new tokens after refresh.
        """
        # Reinitialize client to ensure we're using the latest token
        if self.company.access_token:
            self._initialize_client()
        
        logger.debug(f"Token validated for company {self.company.id}")

    def sync_all(self, start_date: Optional[datetime] = None, 
                 end_date: Optional[datetime] = None) -> Dict:
        """
        Sync all data from QuickBooks
        
        Strategy:
        1. Sync chart of accounts first (required for categorization)
        2. Sync transactions
        
        Args:
            start_date: Optional start date for initial sync
            end_date: Optional end date
            
        Returns:
            Dict with sync statistics
        """
        if not self.client:
            logger.error("QB client not initialized")
            return {'success': False, 'error': 'Client not initialized'}
        
        # Check token before starting sync
        self._ensure_token_valid()
        
        # Default date range: last 90 days if no dates provided
        if not end_date:
            end_date = datetime.utcnow()
        if not start_date:
            start_date = end_date - timedelta(days=90)
        
        logger.info(f"Starting sync for company {self.company.id} from {start_date} to {end_date}")
        
        try:
            # Step 1: Sync accounts first (required for categorization)
            account_result = self.sync_accounts()
            
            # Step 2: Sync transactions
            # Token will be checked and refreshed automatically if needed
            txn_result = self.sync_transactions(start_date, end_date)
            
            # Update company sync status
            self.company.update_sync_status('success')
            db.session.commit()
            
            return {
                'success': True,
                'accounts': account_result,
                'transactions': txn_result,
                'timestamp': datetime.utcnow().isoformat()
            }
            
        except TokenRefreshError as e:
            logger.error(f"Token refresh failed during sync for company {self.company.id}: {e}")
            self.company.update_sync_status('error', f"Token refresh failed: {e}")
            db.session.commit()
            return {
                'success': False,
                'error': str(e),
                'error_type': 'token_refresh',
                'accounts': self.sync_stats['accounts'],
                'transactions': self.sync_stats['transactions']
            }
        except Exception as e:
            logger.error(f"Sync failed for company {self.company.id}: {e}")
            self.company.update_sync_status('error', str(e))
            db.session.commit()
            return {
                'success': False,
                'error': str(e),
                'accounts': self.sync_stats['accounts'],
                'transactions': self.sync_stats['transactions']
            }
    
    def sync_accounts(self) -> Dict:
        """
        Sync chart of accounts using CDC approach
        
        Uses ChangedSince parameter to get only modified accounts
        Falls back to full sync on first run
        
        Returns:
            Dict with sync statistics
        """
        logger.info(f"Syncing accounts for company {self.company.id}")
        
        try:
            # Build query with CDC if we have a last sync time
            last_sync = self.company.last_sync_at
            
            if last_sync:
                # CDC approach - get only changed accounts
                changed_since = last_sync.strftime('%Y-%m-%dT%H:%M:%S')
                query = f"SELECT * FROM Account WHERE MetaData.LastUpdatedTime >= '{changed_since}'"
                logger.info(f"Using CDC for accounts, changed since: {changed_since}")
            else:
                # Full sync on first run
                query = "SELECT * FROM Account WHERE Active = true"
                logger.info("Full sync for accounts (first run)")
            
            # Fetch accounts using Query API with pagination
            qb_accounts = self._fetch_paginated(
                QBAccount, 
                query,
                page_size=self.PAGE_SIZE
            )
            
            created = 0
            updated = 0
            errors = 0
            
            for qb_account in qb_accounts:
                try:
                    result = self._upsert_account(qb_account)
                    if result == 'created':
                        created += 1
                    elif result == 'updated':
                        updated += 1
                except Exception as e:
                    logger.error(f"Error processing account {getattr(qb_account, 'Id', 'unknown')}: {e}")
                    errors += 1
            
            db.session.commit()
            
            self.sync_stats['accounts'] = {
                'created': created,
                'updated': updated,
                'errors': errors,
                'total': created + updated
            }
            
            logger.info(f"Account sync complete: {created} created, {updated} updated, {errors} errors")
            return self.sync_stats['accounts']
            
        except Exception as e:
            logger.error(f"Account sync failed: {e}")
            db.session.rollback()
            self.sync_stats['accounts']['errors'] += 1
            raise
    
    def sync_transactions(self, start_date: datetime, end_date: datetime) -> Dict:
        """
        Sync transactions using CDC approach
        
        Fetches:
        - Purchases (expenses, bills paid)
        - Deposits (income)
        - Journal Entries
        - Payments
        
        Args:
            start_date: Start date for sync
            end_date: End date for sync
            
        Returns:
            Dict with sync statistics
        """
        logger.info(f"Syncing transactions for company {self.company.id} from {start_date} to {end_date}")
        
        total_created = 0
        total_updated = 0
        total_errors = 0
        total_skipped = 0
        
        # Transaction types to sync
        txn_types = [
            ('Purchase', 'expense'),
            ('Deposit', 'income'),
            ('JournalEntry', 'journal'),
            ('Payment', 'payment')
        ]
        
        start_str = start_date.strftime('%Y-%m-%d')
        end_str = end_date.strftime('%Y-%m-%d')
        
        for qb_entity, txn_type in txn_types:
            try:
                logger.info(f"Syncing {qb_entity} transactions...")
                
                # Build CDC query
                last_sync = self.company.last_sync_at
                if last_sync:
                    changed_since = last_sync.strftime('%Y-%m-%dT%H:%M:%S')
                    query = f"SELECT * FROM {qb_entity} WHERE MetaData.LastUpdatedTime >= '{changed_since}' AND TxnDate >= '{start_str}' AND TxnDate <= '{end_str}'"
                else:
                    query = f"SELECT * FROM {qb_entity} WHERE TxnDate >= '{start_str}' AND TxnDate <= '{end_str}'"
                
                # Get entity class
                entity_class = self._get_entity_class(qb_entity)
                
                # Fetch with pagination
                qb_transactions = self._fetch_paginated(
                    entity_class,
                    query,
                    page_size=self.PAGE_SIZE
                )
                
                for qb_txn in qb_transactions:
                    try:
                        result = self._upsert_transaction(qb_txn, txn_type)
                        if result == 'created':
                            total_created += 1
                        elif result == 'updated':
                            total_updated += 1
                        elif result == 'skipped':
                            total_skipped += 1
                    except Exception as e:
                        logger.error(f"Error processing transaction {getattr(qb_txn, 'Id', 'unknown')}: {e}")
                        total_errors += 1
                
                db.session.commit()
                logger.info(f"Synced {len(qb_transactions)} {qb_entity} transactions")
                
            except Exception as e:
                logger.error(f"Failed to sync {qb_entity}: {e}")
                total_errors += 1
        
        self.sync_stats['transactions'] = {
            'created': total_created,
            'updated': total_updated,
            'errors': total_errors,
            'skipped': total_skipped,
            'total': total_created + total_updated
        }
        
        logger.info(f"Transaction sync complete: {total_created} created, {total_updated} updated, "
                   f"{total_skipped} skipped, {total_errors} errors")
        return self.sync_stats['transactions']
    
    def _fetch_paginated(self, entity_class, base_query: str, 
                         page_size: int = 100) -> List:
        """
        Fetch entities using Query API with pagination
        
        QuickBooks Query API supports pagination via STARTPOSITION and MAXRESULTS
        
        Args:
            entity_class: QB entity class (Account, Purchase, etc.)
            base_query: Base query string
            page_size: Number of records per page
            
        Returns:
            List of QB entities
        """
        results = []
        start_position = 1
        page = 0
        
        while page < self.MAX_PAGES:
            try:
                # Check token every few pages (sync may take time)
                if page > 0 and page % 3 == 0:
                    self._ensure_token_valid()
                
                # Build paginated query
                paginated_query = f"{base_query} STARTPOSITION {start_position} MAXRESULTS {page_size}"
                
                # Execute query
                page_results = entity_class.where(paginated_query, qb=self.client)
                
                if not page_results:
                    break
                
                results.extend(page_results)
                
                # Check if we got a full page
                if len(page_results) < page_size:
                    break
                
                start_position += page_size
                page += 1
                
                logger.debug(f"Fetched page {page}, total records: {len(results)}")
                
            except Exception as e:
                logger.error(f"Pagination error at position {start_position}: {e}")
                break
        
        logger.info(f"Fetched {len(results)} records using {page} pages")
        return results
    
    def _upsert_account(self, qb_account) -> str:
        """
        Create or update an account
        
        Args:
            qb_account: QB Account object
            
        Returns:
            'created', 'updated', or 'error'
        """
        # Find existing account
        existing = Account.query.filter_by(
            company_id=self.company.id,
            qb_account_id=qb_account.Id
        ).first()
        
        # Get metadata
        last_updated = getattr(qb_account, 'MetaData', None)
        if last_updated:
            last_updated = getattr(last_updated, 'LastUpdatedTime', None)
        
        if existing:
            # Check if actually changed (CDC optimization)
            if last_updated and existing.updated_at:
                # Parse QB timestamp
                try:
                    qb_time = datetime.fromisoformat(last_updated.replace('Z', '+00:00'))
                    if qb_time <= existing.updated_at:
                        return 'updated'  # No change, but still counts as processed
                except:
                    pass  # Proceed with update if parsing fails
            
            # Update existing account
            existing.name = qb_account.Name
            existing.account_type = getattr(qb_account, 'AccountType', 'Other')
            existing.account_sub_type = getattr(qb_account, 'AccountSubType', None)
            existing.current_balance = getattr(qb_account, 'CurrentBalance', 0)
            existing.is_active = getattr(qb_account, 'Active', True)
            existing.last_imported_at = datetime.utcnow()
            
            # Mark bank accounts
            existing.is_bank_account = existing.account_type in ['Bank', 'Credit Card']
            
            return 'updated'
        else:
            # Create new account
            account = Account(
                company_id=self.company.id,
                qb_account_id=qb_account.Id,
                name=qb_account.Name,
                account_type=getattr(qb_account, 'AccountType', 'Other'),
                account_sub_type=getattr(qb_account, 'AccountSubType', None),
                current_balance=getattr(qb_account, 'CurrentBalance', 0) or 0,
                is_active=getattr(qb_account, 'Active', True),
                is_bank_account=getattr(qb_account, 'AccountType', '') in ['Bank', 'Credit Card'],
                last_imported_at=datetime.utcnow()
            )
            db.session.add(account)
            return 'created'
    
    def _upsert_transaction(self, qb_txn, txn_type: str) -> str:
        """
        Create or update a transaction
        
        Args:
            qb_txn: QB transaction object
            txn_type: Transaction type (expense, income, etc.)
            
        Returns:
            'created', 'updated', 'skipped', or 'error'
        """
        qb_id = qb_txn.Id
        
        # Find existing transaction
        existing = Transaction.query.filter_by(
            company_id=self.company.id,
            qb_transaction_id=qb_id
        ).first()
        
        # Get metadata for CDC check
        last_updated = getattr(qb_txn, 'MetaData', None)
        if last_updated:
            last_updated = getattr(last_updated, 'LastUpdatedTime', None)
        
        # Extract transaction data
        txn_data = self._extract_transaction_data(qb_txn, txn_type)
        
        if not txn_data:
            return 'skipped'
        
        if existing:
            # Check if actually changed (CDC optimization)
            if last_updated and existing.updated_at:
                try:
                    qb_time = datetime.fromisoformat(last_updated.replace('Z', '+00:00'))
                    if qb_time <= existing.updated_at and existing.status != 'pending':
                        return 'skipped'  # No change and already processed
                except:
                    pass
            
            # Update existing transaction
            existing.description = txn_data.get('description')
            existing.amount = txn_data.get('amount', 0)
            existing.transaction_date = txn_data.get('transaction_date')
            existing.payee_name = txn_data.get('payee_name')
            existing.bank_account_id = txn_data.get('bank_account_id')
            existing.bank_account_name = txn_data.get('bank_account_name')
            existing.updated_at = datetime.utcnow()
            
            return 'updated'
        else:
            # Create new transaction
            transaction = Transaction(
                company_id=self.company.id,
                qb_transaction_id=qb_id,
                qb_account_id=txn_data.get('qb_account_id'),
                transaction_type=txn_type,
                description=txn_data.get('description'),
                amount=txn_data.get('amount', 0),
                currency='USD',
                transaction_date=txn_data.get('transaction_date'),
                posted_date=txn_data.get('posted_date'),
                payee_name=txn_data.get('payee_name'),
                payee_id=txn_data.get('payee_id'),
                bank_account_id=txn_data.get('bank_account_id'),
                bank_account_name=txn_data.get('bank_account_name'),
                check_number=txn_data.get('check_number'),
                reference_number=txn_data.get('reference_number'),
                status='pending',
                needs_review=True,
                imported_at=datetime.utcnow()
            )
            db.session.add(transaction)
            return 'created'
    
    def _extract_transaction_data(self, qb_txn, txn_type: str) -> Optional[Dict]:
        """
        Extract common transaction fields from QB transaction object
        
        Args:
            qb_txn: QB transaction object
            txn_type: Transaction type
            
        Returns:
            Dict with extracted data or None if invalid
        """
        data = {
            'description': None,
            'amount': 0,
            'transaction_date': None,
            'posted_date': None,
            'payee_name': None,
            'payee_id': None,
            'qb_account_id': None,
            'bank_account_id': None,
            'bank_account_name': None,
            'check_number': None,
            'reference_number': None
        }
        
        try:
            # Description/Private Note
            data['description'] = getattr(qb_txn, 'PrivateNote', None)
            if not data['description'] and hasattr(qb_txn, 'Memo'):
                data['description'] = qb_txn.Memo
            
            # Amount
            data['amount'] = getattr(qb_txn, 'TotalAmt', 0)
            if data['amount'] is None:
                data['amount'] = 0
            
            # Transaction Date
            txn_date = getattr(qb_txn, 'TxnDate', None)
            if txn_date:
                if isinstance(txn_date, str):
                    data['transaction_date'] = datetime.strptime(txn_date, '%Y-%m-%d').date()
                else:
                    data['transaction_date'] = txn_date
            
            # Payee/Entity
            if hasattr(qb_txn, 'EntityRef'):
                entity_ref = qb_txn.EntityRef
                if hasattr(entity_ref, 'name'):
                    data['payee_name'] = entity_ref.name
                elif hasattr(entity_ref, 'value'):
                    data['payee_id'] = entity_ref.value
            
            # Vendor (for Purchases)
            if hasattr(qb_txn, 'VendorRef'):
                vendor_ref = qb_txn.VendorRef
                if hasattr(vendor_ref, 'name'):
                    data['payee_name'] = vendor_ref.name
                data['payee_id'] = getattr(vendor_ref, 'value', None)
            
            # Customer (for Deposits/Payments)
            if hasattr(qb_txn, 'CustomerRef'):
                customer_ref = qb_txn.CustomerRef
                if hasattr(customer_ref, 'name'):
                    data['payee_name'] = customer_ref.name
                data['payee_id'] = getattr(customer_ref, 'value', None)
            
            # Bank Account
            if hasattr(qb_txn, 'AccountRef'):
                account_ref = qb_txn.AccountRef
                data['qb_account_id'] = getattr(account_ref, 'value', None)
                data['bank_account_name'] = getattr(account_ref, 'name', None)
                if data['qb_account_id']:
                    data['bank_account_id'] = data['qb_account_id']
            
            # Payment Method
            if hasattr(qb_txn, 'PaymentMethodRef'):
                payment_ref = qb_txn.PaymentMethodRef
                # Could map to specific payment types
            
            # Check number
            data['check_number'] = getattr(qb_txn, 'DocNumber', None)
            data['reference_number'] = getattr(qb_txn, 'PaymentRefNum', None)
            
            # For Journal Entries, extract from Line items
            if txn_type == 'journal' and hasattr(qb_txn, 'Line'):
                # Journal entries have multiple lines - we may need special handling
                # For now, use the first line description if no main description
                lines = qb_txn.Line
                if lines and not data['description']:
                    first_line = lines[0] if isinstance(lines, list) else lines
                    if hasattr(first_line, 'Description'):
                        data['description'] = first_line.Description
            
            return data
            
        except Exception as e:
            logger.error(f"Error extracting transaction data: {e}")
            return None
    
    def _get_entity_class(self, entity_name: str):
        """
        Get the QB entity class by name
        
        Args:
            entity_name: Name of entity (Purchase, Deposit, etc.)
            
        Returns:
            Entity class
        """
        entity_map = {
            'Account': QBAccount,
            'Purchase': Purchase,
            'Deposit': Deposit,
            'JournalEntry': JournalEntry,
            'Payment': Payment
        }
        return entity_map.get(entity_name, Purchase)