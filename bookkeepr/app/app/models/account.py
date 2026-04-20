"""Account Model (Chart of Accounts)"""
from datetime import datetime
from extensions import db


class Account(db.Model):
    """QuickBooks Chart of Accounts entry"""
    
    __tablename__ = 'accounts'
    
    id = db.Column(db.Integer, primary_key=True)
    company_id = db.Column(db.Integer, db.ForeignKey('companies.id'), nullable=False, index=True)
    
    # QuickBooks Account Info
    qbo_account_id = db.Column(db.String(50), nullable=False, index=True)
    name = db.Column(db.String(255), nullable=False)
    account_type = db.Column(db.String(100))  # Expense, Income, Asset, etc.
    account_sub_type = db.Column(db.String(100))
    
    # Classification
    classification = db.Column(db.String(50))  # Asset, Liability, Equity, Revenue, Expense
    
    # Balances
    current_balance = db.Column(db.Numeric(19, 2), default=0)
    current_balance_with_sub_accounts = db.Column(db.Numeric(19, 2), default=0)
    
    # Status
    is_active = db.Column(db.Boolean, default=True)
    fully_qualified_name = db.Column(db.String(500))
    
    # Hierarchy
    parent_id = db.Column(db.Integer, db.ForeignKey('accounts.id'), nullable=True)
    level = db.Column(db.Integer, default=0)
    
    # Metadata
    description = db.Column(db.Text)
    account_number = db.Column(db.String(50))
    tax_code = db.Column(db.String(50))
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_sync_at = db.Column(db.DateTime)
    
    # Relationships
    children = db.relationship('Account', backref=db.backref('parent', remote_side=[id]), lazy='dynamic')
    
    __table_args__ = (
        db.UniqueConstraint('company_id', 'qbo_account_id', name='uix_company_account'),
    )
    
    def __repr__(self):
        return f'<Account {self.name} ({self.account_type})>'
    
    def to_dict(self):
        """Serialize to dictionary"""
        return {
            'id': self.id,
            'qbo_account_id': self.qbo_account_id,
            'name': self.name,
            'account_type': self.account_type,
            'account_sub_type': self.account_sub_type,
            'classification': self.classification,
            'current_balance': float(self.current_balance) if self.current_balance else 0,
            'is_active': self.is_active,
            'fully_qualified_name': self.fully_qualified_name,
            'account_number': self.account_number,
            'description': self.description,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
