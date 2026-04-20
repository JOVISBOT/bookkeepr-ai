"""
Company Model - QuickBooks Connection
"""
from app import db
from datetime import datetime
import json


class Company(db.Model):
    """
    Represents a QuickBooks company connection
    Each user can have multiple companies (based on tier)
    """
    __tablename__ = 'companies'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    
    # Company Info
    name = db.Column(db.String(256), nullable=False)
    legal_name = db.Column(db.String(256))
    company_type = db.Column(db.String(50))  # LLC, Corp, etc.
    
    # QuickBooks
    qb_type = db.Column(db.String(10), default='QBO')  # QBO or QBD
    realm_id = db.Column(db.String(64), unique=True, nullable=False, index=True)
    
    # OAuth Tokens (encrypted in production)
    access_token = db.Column(db.Text)
    refresh_token = db.Column(db.Text)
    token_expires_at = db.Column(db.DateTime)
    
    # Connection Status
    is_connected = db.Column(db.Boolean, default=True)
    last_sync_at = db.Column(db.DateTime)
    last_sync_status = db.Column(db.String(20), default='pending')  # pending, success, error
    last_sync_error = db.Column(db.Text)
    
    # Sync Settings
    sync_frequency = db.Column(db.String(20), default='hourly')  # hourly, daily
    sync_enabled = db.Column(db.Boolean, default=True)
    
    # Company Details (cached from QB)
    fiscal_year_start_month = db.Column(db.Integer, default=1)
    tax_form = db.Column(db.String(50))
    industry = db.Column(db.String(100))
    currency = db.Column(db.String(3), default='USD')
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    disconnected_at = db.Column(db.DateTime)
    
    # Relationships
    transactions = db.relationship('Transaction', backref='company', lazy='dynamic', cascade='all, delete-orphan')
    accounts = db.relationship('Account', backref='company', lazy='dynamic', cascade='all, delete-orphan')
    
    def needs_token_refresh(self):
        """Check if access token needs refresh (expires in < 5 minutes)"""
        if not self.token_expires_at:
            return True
        from datetime import timedelta
        return datetime.utcnow() > self.token_expires_at - timedelta(minutes=5)
    
    def update_sync_status(self, status, error=None):
        """Update sync status and timestamp"""
        self.last_sync_at = datetime.utcnow()
        self.last_sync_status = status
        self.last_sync_error = error if error else None
    
    def get_chart_of_accounts(self):
        """Get active accounts ordered by type"""
        return self.accounts.filter_by(is_active=True).order_by(Account.account_type, Account.name).all()
    
    @property
    def pending_transactions_count(self):
        """Count uncategorized transactions"""
        return self.transactions.filter_by(category_id=None).count()
    
    @property
    def total_transactions_count(self):
        """Total transactions synced"""
        return self.transactions.count()
    
    def to_dict(self):
        """Serialize company to dict"""
        return {
            'id': self.id,
            'name': self.name,
            'qb_type': self.qb_type,
            'realm_id': self.realm_id,
            'is_connected': self.is_connected,
            'last_sync_at': self.last_sync_at.isoformat() if self.last_sync_at else None,
            'last_sync_status': self.last_sync_status,
            'pending_count': self.pending_transactions_count,
            'total_count': self.total_transactions_count,
            'currency': self.currency
        }
    
    def __repr__(self):
        return f'<Company {self.name} ({self.realm_id})>'