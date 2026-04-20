"""
Transaction Model
"""
from app import db
from datetime import datetime


class Transaction(db.Model):
    """
    Financial transactions imported from QuickBooks
    """
    __tablename__ = 'transactions'
    
    id = db.Column(db.Integer, primary_key=True)
    company_id = db.Column(db.Integer, db.ForeignKey('companies.id'), nullable=False, index=True)
    
    # QuickBooks IDs
    qb_transaction_id = db.Column(db.String(128), unique=True, index=True)
    qb_account_id = db.Column(db.String(128), index=True)
    
    # Transaction Details
    transaction_type = db.Column(db.String(50), nullable=False, index=True)  # expense, income, transfer, etc.
    description = db.Column(db.Text)
    amount = db.Column(db.Numeric(15, 2), nullable=False)
    currency = db.Column(db.String(3), default='USD')
    
    # Dates
    transaction_date = db.Column(db.Date, nullable=False, index=True)
    posted_date = db.Column(db.Date)
    
    # Vendor/Payee
    payee_name = db.Column(db.String(256), index=True)
    payee_id = db.Column(db.String(128))
    
    # Category (from our system, not QB)
    category_id = db.Column(db.Integer, db.ForeignKey('accounts.id'))
    category_confidence = db.Column(db.Float, default=0.0)  # AI confidence score
    category_suggestions = db.Column(db.JSON)  # Top 3 suggestions with scores
    
    # Bank/Meta
    bank_account_id = db.Column(db.String(128), index=True)
    bank_account_name = db.Column(db.String(256))
    check_number = db.Column(db.String(64))
    reference_number = db.Column(db.String(128))
    
    # AI Processing
    ai_processed = db.Column(db.Boolean, default=False)
    ai_rules_matched = db.Column(db.JSON)  # Which rules matched
    needs_review = db.Column(db.Boolean, default=True, index=True)
    review_reason = db.Column(db.String(256))
    
    # Reconciliation
    is_reconciled = db.Column(db.Boolean, default=False, index=True)
    reconciled_at = db.Column(db.DateTime)
    reconciled_by_user_id = db.Column(db.Integer)
    
    # Status
    status = db.Column(db.String(20), default='pending', index=True)  # pending, categorized, reviewed, approved
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    imported_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    category = db.relationship('Account', backref='transactions')
    
    @classmethod
    def get_uncategorized(cls, company_id, limit=100):
        """Get uncategorized transactions for review"""
        return cls.query.filter_by(
            company_id=company_id,
            needs_review=True,
            category_id=None
        ).order_by(cls.transaction_date.desc()).limit(limit).all()
    
    @classmethod
    def get_by_date_range(cls, company_id, start_date, end_date):
        """Get transactions in date range"""
        return cls.query.filter(
            cls.company_id == company_id,
            cls.transaction_date >= start_date,
            cls.transaction_date <= end_date
        ).order_by(cls.transaction_date.desc()).all()
    
    def categorize(self, account_id, confidence=1.0, user_id=None):
        """Categorize transaction"""
        self.category_id = account_id
        self.category_confidence = confidence
        self.needs_review = confidence < 0.8  # Review if low confidence
        self.ai_processed = True
        self.status = 'categorized'
        self.updated_at = datetime.utcnow()
    
    def approve(self, user_id=None):
        """Mark as reviewed and approved"""
        self.needs_review = False
        self.status = 'approved'
        self.updated_at = datetime.utcnow()
    
    def reconcile(self, user_id=None):
        """Mark as reconciled"""
        self.is_reconciled = True
        self.reconciled_at = datetime.utcnow()
        self.reconciled_by_user_id = user_id
    
    def to_dict(self):
        """Serialize to dict"""
        return {
            'id': self.id,
            'qb_transaction_id': self.qb_transaction_id,
            'transaction_type': self.transaction_type,
            'description': self.description,
            'amount': float(self.amount),
            'currency': self.currency,
            'transaction_date': self.transaction_date.isoformat() if self.transaction_date else None,
            'payee_name': self.payee_name,
            'category_id': self.category_id,
            'category_confidence': self.category_confidence,
            'needs_review': self.needs_review,
            'is_reconciled': self.is_reconciled,
            'status': self.status,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
    
    def __repr__(self):
        return f'<Transaction {self.description} ${self.amount}>'