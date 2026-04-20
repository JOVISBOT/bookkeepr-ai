"""Transaction Model"""
from datetime import datetime
from extensions import db


class Transaction(db.Model):
    """Financial transaction imported from QuickBooks"""
    
    __tablename__ = 'transactions'
    
    id = db.Column(db.Integer, primary_key=True)
    company_id = db.Column(db.Integer, db.ForeignKey('companies.id'), nullable=False, index=True)
    account_id = db.Column(db.Integer, db.ForeignKey('accounts.id'), nullable=True, index=True)
    
    # QuickBooks Transaction Info
    qbo_transaction_id = db.Column(db.String(50), nullable=False, index=True)
    transaction_type = db.Column(db.String(50), nullable=False, index=True)  # Purchase, JournalEntry, Deposit, etc.
    
    # Transaction Details
    transaction_date = db.Column(db.Date, nullable=False, index=True)
    amount = db.Column(db.Numeric(19, 2), nullable=False)
    description = db.Column(db.Text)
    memo = db.Column(db.Text)
    
    # Payee/Vendor
    vendor_name = db.Column(db.String(255), index=True)
    vendor_id = db.Column(db.String(50))
    customer_name = db.Column(db.String(255))
    customer_id = db.Column(db.String(50))
    
    # Category/Account Info
    account_name = db.Column(db.String(255))
    category = db.Column(db.String(255), index=True)
    
    # Categorization Status
    categorization_status = db.Column(db.String(50), default='uncategorized', index=True)  # uncategorized, suggested, categorized
    suggested_category = db.Column(db.String(255))
    suggested_confidence = db.Column(db.Numeric(5, 2))  # 0-100 confidence score
    categorized_by = db.Column(db.String(50))  # ai, user, rule
    categorized_at = db.Column(db.DateTime)
    
    # Review Status
    review_status = db.Column(db.String(50), default='pending', index=True)  # pending, approved, flagged
    reviewed_by_user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    reviewed_at = db.Column(db.DateTime)
    review_notes = db.Column(db.Text)
    
    # Document/Receipt
    has_attachment = db.Column(db.Boolean, default=False)
    attachment_url = db.Column(db.Text)
    
    # Raw Data
    raw_data = db.Column(db.JSON)  # Store full QBO response for reference
    
    # Sync Info
    last_sync_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    reviewed_by = db.relationship('User', foreign_keys=[reviewed_by_user_id])
    
    __table_args__ = (
        db.UniqueConstraint('company_id', 'qbo_transaction_id', name='uix_company_transaction'),
        db.Index('ix_transactions_date_type', 'transaction_date', 'transaction_type'),
        db.Index('ix_transactions_vendor_status', 'vendor_name', 'categorization_status'),
    )
    
    def __repr__(self):
        return f'<Transaction {self.qbo_transaction_id}: {self.amount}>'
    
    @property
    def is_expense(self):
        """Check if transaction is an expense"""
        return self.amount < 0 or self.transaction_type in ['Purchase', 'BillPayment', 'Check']
    
    @property
    def is_income(self):
        """Check if transaction is income"""
        return self.amount > 0 and self.transaction_type in ['Invoice', 'SalesReceipt', 'Deposit']
    
    def to_dict(self):
        """Serialize to dictionary"""
        return {
            'id': self.id,
            'qbo_transaction_id': self.qbo_transaction_id,
            'transaction_type': self.transaction_type,
            'transaction_date': self.transaction_date.isoformat() if self.transaction_date else None,
            'amount': float(self.amount) if self.amount else 0,
            'description': self.description,
            'memo': self.memo,
            'vendor_name': self.vendor_name,
            'customer_name': self.customer_name,
            'category': self.category,
            'categorization_status': self.categorization_status,
            'suggested_category': self.suggested_category,
            'suggested_confidence': float(self.suggested_confidence) if self.suggested_confidence else None,
            'review_status': self.review_status,
            'has_attachment': self.has_attachment,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'categorized_at': self.categorized_at.isoformat() if self.categorized_at else None
        }
