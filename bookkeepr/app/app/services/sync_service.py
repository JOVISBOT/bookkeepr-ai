"""Sync Service"""
from datetime import datetime, timedelta
from flask import current_app
from extensions import db
from app.models.company import Company
from app.models.account import Account
from app.models.transaction import Transaction
from app.services.quickbooks_service import QuickBooksService


class SyncService:
    """Handle data synchronization between BookKeepr and QuickBooks"""
    
    def __init__(self, company):
        self.company = company
        self.qb_service = QuickBooksService(
            access_token=company.access_token,
            realm_id=company.qbo_realm_id,
            refresh_token=company.refresh_token
        )
    
    def sync_company_info(self):
        """Sync company information from QBO"""
        try:
            company_info = self.qb_service.get_company_info()
            
            if company_info:
                self.company.qbo_company_name = getattr(company_info, 'CompanyName', None)
                # Company address and other details would be extracted here
                self.company.is_connected = True
                self.company.last_sync_at = datetime.utcnow()
                db.session.commit()
                
                return {
                    'success': True,
                    'message': 'Company info synced successfully',
                    'data': {
                        'name': self.company.qbo_company_name
                    }
                }
            else:
                return {
                    'success': False,
                    'message': 'Could not retrieve company info'
                }
                
        except Exception as e:
            current_app.logger.error(f"Company sync failed: {str(e)}")
            return {
                'success': False,
                'message': f'Sync failed: {str(e)}'
            }
    
    def sync_chart_of_accounts(self):
        """Sync chart of accounts from QBO"""
        try:
            qb_accounts = self.qb_service.get_chart_of_accounts(active_only=True)
            
            synced_count = 0
            for qb_account in qb_accounts:
                # Check if account already exists
                existing = Account.query.filter_by(
                    company_id=self.company.id,
                    qbo_account_id=str(qb_account.Id)
                ).first()
                
                if existing:
                    # Update existing
                    existing.name = qb_account.Name
                    existing.account_type = getattr(qb_account, 'AccountType', None)
                    existing.account_sub_type = getattr(qb_account, 'AccountSubType', None)
                    existing.classification = getattr(qb_account, 'Classification', None)
                    existing.current_balance = getattr(qb_account, 'CurrentBalance', 0)
                    existing.is_active = getattr(qb_account, 'Active', True)
                    existing.updated_at = datetime.utcnow()
                    existing.last_sync_at = datetime.utcnow()
                else:
                    # Create new
                    new_account = Account(
                        company_id=self.company.id,
                        qbo_account_id=str(qb_account.Id),
                        name=qb_account.Name,
                        account_type=getattr(qb_account, 'AccountType', None),
                        account_sub_type=getattr(qb_account, 'AccountSubType', None),
                        classification=getattr(qb_account, 'Classification', None),
                        current_balance=getattr(qb_account, 'CurrentBalance', 0),
                        is_active=getattr(qb_account, 'Active', True),
                        fully_qualified_name=getattr(qb_account, 'FullyQualifiedName', None),
                        description=getattr(qb_account, 'Description', None),
                        account_number=getattr(qb_account, 'AcctNum', None),
                        tax_code=getattr(qb_account, 'TaxCodeRef', None),
                        last_sync_at=datetime.utcnow()
                    )
                    db.session.add(new_account)
                    synced_count += 1
            
            db.session.commit()
            
            return {
                'success': True,
                'message': f'Synced {synced_count} new accounts',
                'data': {
                    'new_accounts': synced_count,
                    'total_accounts': Account.query.filter_by(company_id=self.company.id).count()
                }
            }
            
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Chart of accounts sync failed: {str(e)}")
            return {
                'success': False,
                'message': f'Sync failed: {str(e)}'
            }
    
    def sync_transactions(self, days_back=90):
        """Sync transactions from QBO"""
        try:
            end_date = datetime.utcnow().date()
            start_date = end_date - timedelta(days=days_back)
            
            qb_transactions = self.qb_service.get_transactions(
                start_date=start_date.isoformat(),
                end_date=end_date.isoformat(),
                limit=1000
            )
            
            synced_count = 0
            for qb_txn in qb_transactions:
                # Extract transaction ID and type
                txn_id = str(qb_txn.Id)
                txn_type = qb_txn.__class__.__name__
                
                # Check if already exists
                existing = Transaction.query.filter_by(
                    company_id=self.company.id,
                    qbo_transaction_id=txn_id
                ).first()
                
                if existing:
                    # Update existing transaction
                    existing.amount = getattr(qb_txn, 'TotalAmt', 0)
                    existing.updated_at = datetime.utcnow()
                    existing.last_sync_at = datetime.utcnow()
                else:
                    # Create new transaction
                    new_txn = self._create_transaction_from_qbo(qb_txn, txn_id, txn_type)
                    db.session.add(new_txn)
                    synced_count += 1
            
            db.session.commit()
            
            return {
                'success': True,
                'message': f'Synced {synced_count} new transactions',
                'data': {
                    'new_transactions': synced_count,
                    'total_transactions': Transaction.query.filter_by(company_id=self.company.id).count()
                }
            }
            
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Transaction sync failed: {str(e)}")
            return {
                'success': False,
                'message': f'Sync failed: {str(e)}'
            }
    
    def _create_transaction_from_qbo(self, qb_txn, txn_id, txn_type):
        """Convert QBO transaction to our model"""
        
        # Get common fields
        txn_date = getattr(qb_txn, 'TxnDate', None)
        total_amt = getattr(qb_txn, 'TotalAmt', 0)
        
        # Get vendor/payee info
        vendor_name = None
        if hasattr(qb_txn, 'VendorRef') and qb_txn.VendorRef:
            vendor_name = getattr(qb_txn.VendorRef, 'name', None)
        
        # Get account/category info
        account_name = None
        category = None
        if hasattr(qb_txn, 'AccountRef') and qb_txn.AccountRef:
            account_name = getattr(qb_txn.AccountRef, 'name', None)
        
        return Transaction(
            company_id=self.company.id,
            qbo_transaction_id=txn_id,
            transaction_type=txn_type,
            transaction_date=txn_date,
            amount=total_amt,
            description=getattr(qb_txn, 'PrivateNote', None),
            memo=getattr(qb_txn, 'Memo', None),
            vendor_name=vendor_name,
            account_name=account_name,
            category=category,
            categorization_status='uncategorized',
            raw_data=qb_txn.to_dict() if hasattr(qb_txn, 'to_dict') else None,
            last_sync_at=datetime.utcnow()
        )
    
    def run_full_sync(self):
        """Run complete sync: company, accounts, and transactions"""
        results = {
            'company': self.sync_company_info(),
            'accounts': self.sync_chart_of_accounts(),
            'transactions': self.sync_transactions()
        }
        
        # Update company sync status
        self.company.sync_status = 'success'
        self.company.last_sync_at = datetime.utcnow()
        db.session.commit()
        
        return results
