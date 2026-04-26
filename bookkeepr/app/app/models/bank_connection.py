"""
Bank Connection Model
Stores Plaid connections
"""
from datetime import datetime
from extensions import db


class BankConnection(db.Model):
    """Plaid bank connection"""
    
    __tablename__ = 'bank_connections'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    plaid_access_token = db.Column(db.String(255), nullable=False)
    plaid_item_id = db.Column(db.String(255), nullable=False)
    institution_name = db.Column(db.String(100), nullable=False)
    institution_id = db.Column(db.String(100))
    status = db.Column(db.String(20), default='active')  # active, disconnected, error
    last_sync = db.Column(db.DateTime)
    error_message = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = db.relationship('User', backref='bank_connections')
    accounts = db.relationship('BankAccount', backref='connection', lazy=True, cascade='all, delete-orphan')
    
    def to_dict(self):
        return {
            'id': self.id,
            'institution_name': self.institution_name,
            'institution_id': self.institution_id,
            'status': self.status,
            'last_sync': self.last_sync.isoformat() if self.last_sync else None,
            'created_at': self.created_at.isoformat(),
            'accounts': [account.to_dict() for account in self.accounts]
        }


class BankAccount(db.Model):
    """Individual bank account (checking, savings, credit card)"""
    
    __tablename__ = 'bank_accounts'
    
    id = db.Column(db.Integer, primary_key=True)
    connection_id = db.Column(db.Integer, db.ForeignKey('bank_connections.id'), nullable=False)
    plaid_account_id = db.Column(db.String(255), nullable=False, unique=True)
    name = db.Column(db.String(100), nullable=False)
    official_name = db.Column(db.String(255))
    account_type = db.Column(db.String(50))  # depository, credit, loan, etc.
    account_subtype = db.Column(db.String(50))  # checking, savings, credit card
    mask = db.Column(db.String(20))  # last 4 digits
    current_balance = db.Column(db.Numeric(12, 2))
    available_balance = db.Column(db.Numeric(12, 2))
    currency = db.Column(db.String(3), default='USD')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    transactions = db.relationship('BankTransaction', backref='account', lazy=True)
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'official_name': self.official_name,
            'type': self.account_type,
            'subtype': self.account_subtype,
            'mask': self.mask,
            'current_balance': float(self.current_balance) if self.current_balance else None,
            'available_balance': float(self.available_balance) if self.available_balance else None,
            'currency': self.currency
        }


class BankTransaction(db.Model):
    """Transactions imported from bank"""
    
    __tablename__ = 'bank_transactions'
    
    id = db.Column(db.Integer, primary_key=True)
    account_id = db.Column(db.String(255), db.ForeignKey('bank_accounts.plaid_account_id'), nullable=False)
    plaid_transaction_id = db.Column(db.String(255), nullable=False, unique=True)
    
    # Transaction details
    amount = db.Column(db.Numeric(10, 2), nullable=False)
    is_debit = db.Column(db.Boolean, default=True)
    date = db.Column(db.Date, nullable=False)
    description = db.Column(db.String(255), nullable=False)
    merchant_name = db.Column(db.String(255))
    category = db.Column(db.String(100))  # Plaid category
    
    # AI categorization
    ai_category = db.Column(db.String(100))
    ai_confidence = db.Column(db.Numeric(3, 2))
    user_category = db.Column(db.String(100))  # User override
    
    # Status
    pending = db.Column(db.Boolean, default=False)
    reviewed = db.Column(db.Boolean, default=False)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'plaid_transaction_id': self.plaid_transaction_id,
            'amount': float(self.amount),
            'is_debit': self.is_debit,
            'date': self.date.isoformat(),
            'description': self.description,
            'merchant_name': self.merchant_name,
            'category': self.category,
            'ai_category': self.ai_category,
            'ai_confidence': float(self.ai_confidence) if self.ai_confidence else None,
            'user_category': self.user_category,
            'pending': self.pending,
            'reviewed': self.reviewed
        }
