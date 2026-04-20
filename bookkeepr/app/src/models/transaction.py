"""
Transaction model for imported QuickBooks transactions
"""
from datetime import datetime
from enum import Enum
from ..extensions import db


class TransactionStatus(str, Enum):
    """Transaction categorization status."""
    IMPORTED = 'imported'        # Just imported, not categorized
    SUGGESTED = 'suggested'       # AI suggested category, awaiting confirmation
    CATEGORIZED = 'categorized'   # Category assigned (auto or manual)
    REVIEWED = 'reviewed'         # User reviewed and confirmed
    POSTED = 'posted'             # Posted to QuickBooks
    ERROR = 'error'               # Error during processing


class TransactionType(str, Enum):
    """QuickBooks transaction types."""
    EXPENSE = 'expense'
    CHECK = 'check'
    CREDIT_CARD = 'credit_card'
    BILL = 'bill'
    BILL_PAYMENT = 'bill_payment'
    DEPOSIT = 'deposit'
    TRANSFER = 'transfer'
    JOURNAL_ENTRY = 'journal_entry'
    SALES_RECEIPT = 'sales_receipt'
    INVOICE = 'invoice'
    REFUND = 'refund'
    OTHER = 'other'


class Transaction(db.Model):
    """
    Transaction model storing imported QuickBooks transactions.
    Supports AI categorization and review workflow.
    """
    __tablename__ = 'transactions'
    
    id = db.Column(db.Integer, primary_key=True)
    company_id = db.Column(db.Integer, db.ForeignKey('companies.id'), 
                          nullable=False, index=True)
    
    # QuickBooks identifiers
    qbo_id = db.Column(db.String(100), nullable=False, index=True)
    qbo_transaction_type = db.Column(db.String(50))
    
    # Transaction details
    date = db.Column(db.Date, nullable=False, index=True)
    amount = db.Column(db.Numeric(15, 2), nullable=False)
    description = db.Column(db.Text)
    memo = db.Column(db.Text)
    vendor = db.Column(db.String(255), index=True)
    payee = db.Column(db.String(255))
    
    # Categorization
    category = db.Column(db.String(100), index=True)
    category_confidence = db.Column(db.Numeric(3, 2))  # 0.00 to 1.00
    suggested_category = db.Column(db.String(100))
    
    # QuickBooks account info
    account_id = db.Column(db.String(100))
    account_name = db.Column(db.String(255))
    chart_account_id = db.Column(db.String(100))
    chart_account_name = db.Column(db.String(255))
    
    # Transaction type
    transaction_type = db.Column(db.String(50), default=TransactionType.EXPENSE)
    
    # Status tracking
    status = db.Column(db.String(20), default=TransactionStatus.IMPORTED, 
                      nullable=False, index=True)
    
    # Metadata
    source = db.Column(db.String(50), default='qbo')  # qbo, manual, import
    is_split = db.Column(db.Boolean, default=False)
    parent_transaction_id = db.Column(db.Integer, db.ForeignKey('transactions.id'))
    
    # AI/ML fields
    ai_reasoning = db.Column(db.Text)  # Why AI chose this category
    user_corrected = db.Column(db.Boolean, default=False)  # Was this corrected?
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, 
                          onupdate=datetime.utcnow, nullable=False)
    categorized_at = db.Column(db.DateTime)
    reviewed_at = db.Column(db.DateTime)
    
    # Unique constraint
    __table_args__ = (
        db.UniqueConstraint('company_id', 'qbo_id', name='uix_company_transaction'),
        db.CheckConstraint('amount != 0', name='check_nonzero_amount'),
        db.Index('ix_transactions_company_status', 'company_id', 'status'),
        db.Index('ix_transactions_company_date', 'company_id', 'date'),
        db.Index('ix_transactions_review_queue', 'company_id', 'status', 'category_confidence'),
    )
    
    # Relationships
    split_transactions = db.relationship('Transaction', 
                                        backref=db.backref('parent', remote_side=[id]),
                                        lazy='dynamic')
    
    @property
    def needs_review(self):
        """Check if transaction needs user review."""
        return self.status in [TransactionStatus.IMPORTED, TransactionStatus.SUGGESTED]
    
    @property
    def is_categorized(self):
        """Check if transaction has a category."""
        return self.status in [TransactionStatus.CATEGORIZED, 
                              TransactionStatus.REVIEWED, 
                              TransactionStatus.POSTED]
    
    @property
    def display_category(self):
        """Return category to display."""
        return self.category or self.suggested_category or 'Uncategorized'
    
    def categorize(self, category, confidence=1.0, auto=False, reasoning=None):
        """Categorize this transaction."""
        if auto and confidence >= 0.8:
            # Auto-categorize with high confidence
            self.category = category
            self.category_confidence = confidence
            self.status = TransactionStatus.CATEGORIZED
            self.ai_reasoning = reasoning
            self.categorized_at = datetime.utcnow()
        else:
            # Suggest category for review
            self.suggested_category = category
            self.category_confidence = confidence
            self.status = TransactionStatus.SUGGESTED
            self.ai_reasoning = reasoning
    
    def confirm_category(self, category=None):
        """User confirms or changes category."""
        if category:
            self.category = category
            self.user_corrected = (category != self.suggested_category)
        else:
            self.category = self.suggested_category
            self.user_corrected = False
        
        self.status = TransactionStatus.REVIEWED
        self.categorized_at = datetime.utcnow()
        self.reviewed_at = datetime.utcnow()
    
    def to_dict(self):
        """Serialize to dictionary."""
        return {
            'id': self.id,
            'company_id': self.company_id,
            'qbo_id': self.qbo_id,
            'date': self.date.isoformat() if self.date else None,
            'amount': float(self.amount) if self.amount else None,
            'description': self.description,
            'vendor': self.vendor,
            'payee': self.payee,
            'category': self.category,
            'suggested_category': self.suggested_category,
            'display_category': self.display_category,
            'category_confidence': float(self.category_confidence) if self.category_confidence else None,
            'transaction_type': self.transaction_type,
            'status': self.status,
            'account_name': self.account_name,
            'needs_review': self.needs_review,
            'is_categorized': self.is_categorized,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }
    
    def __repr__(self):
        return f'<Transaction {self.qbo_id}: {self.vendor} ${self.amount}>'
