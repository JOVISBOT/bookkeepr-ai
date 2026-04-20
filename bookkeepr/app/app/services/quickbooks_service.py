"""QuickBooks Service"""
from flask import current_app
from quickbooks import QuickBooks
from quickbooks.objects.customer import Customer
from quickbooks.objects.account import Account
from quickbooks.objects.purchase import Purchase
from quickbooks.objects.journalentry import JournalEntry
from quickbooks.objects.deposit import Deposit
from quickbooks.objects.invoice import Invoice
from quickbooks.objects.salesreceipt import SalesReceipt


class QuickBooksService:
    """Handle QuickBooks API operations"""
    
    def __init__(self, access_token, realm_id, refresh_token=None):
        self.access_token = access_token
        self.realm_id = realm_id
        self.refresh_token = refresh_token
        
        sandbox = current_app.config['INTUIT_SANDBOX_MODE']
        
        self.client = QuickBooks(
            auth_client=None,  # We handle auth separately
            refresh_token=refresh_token,
            company_id=realm_id,
            minorversion=65  # API version
        )
        
        # Set access token directly
        self.client.access_token = access_token
        
        # Set sandbox mode
        if sandbox:
            self.client.sandbox = True
    
    def get_company_info(self):
        """Get company information from QuickBooks"""
        try:
            # CompanyInfo is retrieved via special endpoint
            from quickbooks.objects.company_info import CompanyInfo
            company_info = CompanyInfo.all(qb=self.client, max_results=1)
            return company_info[0] if company_info else None
        except Exception as e:
            current_app.logger.error(f"Failed to get company info: {str(e)}")
            return None
    
    def get_chart_of_accounts(self, active_only=True):
        """Get chart of accounts"""
        try:
            query = "SELECT * FROM Account"
            if active_only:
                query += " WHERE Active = true"
            
            accounts = Account.query(
                f"SELECT * FROM Account WHERE Active = true",
                qb=self.client
            )
            return accounts
        except Exception as e:
            current_app.logger.error(f"Failed to get chart of accounts: {str(e)}")
            return []
    
    def get_transactions(self, start_date=None, end_date=None, limit=1000):
        """Get transactions from QuickBooks"""
        transactions = []
        
        try:
            # Get Purchases (expenses, bills paid)
            purchases = self._get_purchases(start_date, end_date, limit)
            transactions.extend(purchases)
            
            # Get Deposits
            deposits = self._get_deposits(start_date, end_date, limit)
            transactions.extend(deposits)
            
            # Get Journal Entries
            journal_entries = self._get_journal_entries(start_date, end_date, limit)
            transactions.extend(journal_entries)
            
            # Get Invoices
            invoices = self._get_invoices(start_date, end_date, limit)
            transactions.extend(invoices)
            
            # Get Sales Receipts
            sales_receipts = self._get_sales_receipts(start_date, end_date, limit)
            transactions.extend(sales_receipts)
            
            return transactions
            
        except Exception as e:
            current_app.logger.error(f"Failed to get transactions: {str(e)}")
            return []
    
    def _get_purchases(self, start_date=None, end_date=None, limit=1000):
        """Get purchase transactions"""
        try:
            # Build query
            query = "SELECT * FROM Purchase"
            conditions = []
            
            if start_date:
                conditions.append(f"TxnDate >= '{start_date}'")
            if end_date:
                conditions.append(f"TxnDate <= '{end_date}'")
            
            if conditions:
                query += " WHERE " + " AND ".join(conditions)
            
            query += f" ORDERBY TxnDate DESC MAXRESULTS {limit}"
            
            purchases = Purchase.query(query, qb=self.client)
            return purchases
        except Exception as e:
            current_app.logger.error(f"Failed to get purchases: {str(e)}")
            return []
    
    def _get_deposits(self, start_date=None, end_date=None, limit=1000):
        """Get deposit transactions"""
        try:
            query = "SELECT * FROM Deposit"
            conditions = []
            
            if start_date:
                conditions.append(f"TxnDate >= '{start_date}'")
            if end_date:
                conditions.append(f"TxnDate <= '{end_date}'")
            
            if conditions:
                query += " WHERE " + " AND ".join(conditions)
            
            query += f" ORDERBY TxnDate DESC MAXRESULTS {limit}"
            
            deposits = Deposit.query(query, qb=self.client)
            return deposits
        except Exception as e:
            current_app.logger.error(f"Failed to get deposits: {str(e)}")
            return []
    
    def _get_journal_entries(self, start_date=None, end_date=None, limit=1000):
        """Get journal entry transactions"""
        try:
            query = "SELECT * FROM JournalEntry"
            conditions = []
            
            if start_date:
                conditions.append(f"TxnDate >= '{start_date}'")
            if end_date:
                conditions.append(f"TxnDate <= '{end_date}'")
            
            if conditions:
                query += " WHERE " + " AND ".join(conditions)
            
            query += f" ORDERBY TxnDate DESC MAXRESULTS {limit}"
            
            entries = JournalEntry.query(query, qb=self.client)
            return entries
        except Exception as e:
            current_app.logger.error(f"Failed to get journal entries: {str(e)}")
            return []
    
    def _get_invoices(self, start_date=None, end_date=None, limit=1000):
        """Get invoice transactions"""
        try:
            query = "SELECT * FROM Invoice"
            conditions = []
            
            if start_date:
                conditions.append(f"TxnDate >= '{start_date}'")
            if end_date:
                conditions.append(f"TxnDate <= '{end_date}'")
            
            if conditions:
                query += " WHERE " + " AND ".join(conditions)
            
            query += f" ORDERBY TxnDate DESC MAXRESULTS {limit}"
            
            invoices = Invoice.query(query, qb=self.client)
            return invoices
        except Exception as e:
            current_app.logger.error(f"Failed to get invoices: {str(e)}")
            return []
    
    def _get_sales_receipts(self, start_date=None, end_date=None, limit=1000):
        """Get sales receipt transactions"""
        try:
            query = "SELECT * FROM SalesReceipt"
            conditions = []
            
            if start_date:
                conditions.append(f"TxnDate >= '{start_date}'")
            if end_date:
                conditions.append(f"TxnDate <= '{end_date}'")
            
            if conditions:
                query += " WHERE " + " AND ".join(conditions)
            
            query += f" ORDERBY TxnDate DESC MAXRESULTS {limit}"
            
            receipts = SalesReceipt.query(query, qb=self.client)
            return receipts
        except Exception as e:
            current_app.logger.error(f"Failed to get sales receipts: {str(e)}")
            return []
    
    def test_connection(self):
        """Test if connection is working"""
        try:
            company_info = self.get_company_info()
            return company_info is not None
        except Exception as e:
            current_app.logger.error(f"Connection test failed: {str(e)}")
            return False
