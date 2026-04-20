"""Company Model"""
from datetime import datetime
from extensions import db


class Company(db.Model):
    """QuickBooks-connected company"""
    
    __tablename__ = 'companies'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    
    # QuickBooks Info
    qbo_realm_id = db.Column(db.String(50), unique=True, nullable=False, index=True)
    qbo_company_name = db.Column(db.String(255))
    qbo_company_address = db.Column(db.Text)
    qbo_company_email = db.Column(db.String(255))
    qbo_company_phone = db.Column(db.String(50))
    
    # OAuth Tokens (encrypted in production)
    access_token = db.Column(db.Text)
    refresh_token = db.Column(db.Text)
    token_expires_at = db.Column(db.DateTime)
    
    # Connection Status
    is_connected = db.Column(db.Boolean, default=False)
    last_sync_at = db.Column(db.DateTime)
    sync_status = db.Column(db.String(50), default='pending')  # pending, syncing, error, success
    
    # Settings
    timezone = db.Column(db.String(50), default='America/Los_Angeles')
    fiscal_year_start = db.Column(db.Integer, default=1)  # Month number (1=Jan)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    disconnected_at = db.Column(db.DateTime)
    
    # Relationships
    accounts = db.relationship('Account', backref='company', lazy='dynamic', cascade='all, delete-orphan')
    transactions = db.relationship('Transaction', backref='company', lazy='dynamic', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Company {self.qbo_company_name or self.qbo_realm_id}>'
    
    @property
    def is_token_expired(self):
        """Check if access token is expired"""
        if not self.token_expires_at:
            return True
        return datetime.utcnow() >= self.token_expires_at
    
    def to_dict(self):
        """Serialize to dictionary"""
        return {
            'id': self.id,
            'qbo_realm_id': self.qbo_realm_id,
            'qbo_company_name': self.qbo_company_name,
            'is_connected': self.is_connected,
            'last_sync_at': self.last_sync_at.isoformat() if self.last_sync_at else None,
            'sync_status': self.sync_status,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
