"""
Account Model - Chart of Accounts
"""
from app import db
from datetime import datetime


class Account(db.Model):
    """
    Chart of Accounts from QuickBooks
    Plus AI learning for categorization
    """
    __tablename__ = 'accounts'
    
    id = db.Column(db.Integer, primary_key=True)
    company_id = db.Column(db.Integer, db.ForeignKey('companies.id'), nullable=False, index=True)
    
    # QuickBooks IDs
    qb_account_id = db.Column(db.String(128), nullable=False, index=True)
    
    # Account Details
    name = db.Column(db.String(256), nullable=False)
    account_type = db.Column(db.String(50), nullable=False, index=True)  # Expense, Income, Asset, etc.
    account_sub_type = db.Column(db.String(100))
    description = db.Column(db.Text)
    
    # Hierarchy
    parent_id = db.Column(db.Integer, db.ForeignKey('accounts.id'))
    level = db.Column(db.Integer, default=0)  # 0 = top level
    
    # Financial
    current_balance = db.Column(db.Numeric(15, 2), default=0)
    currency = db.Column(db.String(3), default='USD')
    
    # Status
    is_active = db.Column(db.Boolean, default=True, index=True)
    is_bank_account = db.Column(db.Boolean, default=False)
    
    # For AI Categorization
    common_keywords = db.Column(db.JSON)  # Learned keywords
    confidence_threshold = db.Column(db.Float, default=0.7)
    
    # Tax
    tax_code = db.Column(db.String(50))
    is_taxable = db.Column(db.Boolean, default=True)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_imported_at = db.Column(db.DateTime)
    
    # Relationships
    parent = db.relationship('Account', remote_side=[id], backref='children')
    
    @classmethod
    def get_expense_accounts(cls, company_id):
        """Get all expense accounts for categorization"""
        return cls.query.filter_by(
            company_id=company_id,
            account_type='Expense',
            is_active=True
        ).order_by(cls.name).all()
    
    @classmethod
    def get_by_type(cls, company_id, account_type):
        """Get accounts by type"""
        return cls.query.filter_by(
            company_id=company_id,
            account_type=account_type,
            is_active=True
        ).order_by(cls.name).all()
    
    def update_balance(self, amount):
        """Update account balance"""
        if self.current_balance is None:
            self.current_balance = 0
        self.current_balance += amount
    
    def to_dict(self):
        """Serialize to dict"""
        return {
            'id': self.id,
            'qb_account_id': self.qb_account_id,
            'name': self.name,
            'account_type': self.account_type,
            'account_sub_type': self.account_sub_type,
            'current_balance': float(self.current_balance) if self.current_balance else 0,
            'currency': self.currency,
            'is_active': self.is_active,
            'is_bank_account': self.is_bank_account,
            'common_keywords': self.common_keywords or []
        }
    
    def __repr__(self):
        return f'<Account {self.name} ({self.account_type})>'