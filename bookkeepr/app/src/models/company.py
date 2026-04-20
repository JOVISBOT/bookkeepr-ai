"""
Company model for QuickBooks connections
"""
from datetime import datetime, timedelta
from cryptography.fernet import Fernet
from flask import current_app
from ..extensions import db


class Company(db.Model):
    """
    Company model representing a connected QuickBooks company.
    Stores OAuth tokens encrypted for security.
    """
    __tablename__ = 'companies'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    
    # QuickBooks identifiers
    realm_id = db.Column(db.String(50), nullable=False, index=True)  # QBO company ID
    company_name = db.Column(db.String(255), nullable=False)
    company_type = db.Column(db.String(20), default='QBO')  # QBO or QBD
    
    # OAuth tokens (encrypted)
    _access_token = db.Column('access_token', db.Text)
    _refresh_token = db.Column('refresh_token', db.Text)
    token_expires_at = db.Column(db.DateTime)
    
    # Connection status
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    is_sandbox = db.Column(db.Boolean, default=True, nullable=False)
    last_sync_at = db.Column(db.DateTime)
    connection_error = db.Column(db.Text)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, 
                          onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    transactions = db.relationship('Transaction', backref='company', lazy='dynamic',
                                cascade='all, delete-orphan')
    categories = db.relationship('Category', backref='company', lazy='dynamic',
                                  cascade='all, delete-orphan')
    
    # Unique constraint on realm_id + user_id
    __table_args__ = (
        db.UniqueConstraint('user_id', 'realm_id', name='uix_user_realm'),
    )
    
    def _get_encryption_key(self):
        """Get encryption key from app config."""
        key = current_app.config.get('ENCRYPTION_KEY')
        if not key:
            raise ValueError("ENCRYPTION_KEY not configured")
        return key.encode() if isinstance(key, str) else key
    
    @property
    def access_token(self):
        """Decrypt and return access token."""
        if not self._access_token:
            return None
        try:
            key = self._get_encryption_key()
            f = Fernet(key)
            return f.decrypt(self._access_token.encode()).decode()
        except Exception:
            return None
    
    @access_token.setter
    def access_token(self, value):
        """Encrypt and store access token."""
        if value:
            key = self._get_encryption_key()
            f = Fernet(key)
            self._access_token = f.encrypt(value.encode()).decode()
        else:
            self._access_token = None
    
    @property
    def refresh_token(self):
        """Decrypt and return refresh token."""
        if not self._refresh_token:
            return None
        try:
            key = self._get_encryption_key()
            f = Fernet(key)
            return f.decrypt(self._refresh_token.encode()).decode()
        except Exception:
            return None
    
    @refresh_token.setter
    def refresh_token(self, value):
        """Encrypt and store refresh token."""
        if value:
            key = self._get_encryption_key()
            f = Fernet(key)
            self._refresh_token = f.encrypt(value.encode()).decode()
        else:
            self._refresh_token = None
    
    @property
    def is_token_expired(self):
        """Check if access token is expired (with 5 min buffer)."""
        if not self.token_expires_at:
            return True
        return datetime.utcnow() >= (self.token_expires_at - timedelta(minutes=5))
    
    @property
    def needs_sync(self):
        """Check if company needs data sync (older than 1 hour)."""
        if not self.last_sync_at:
            return True
        return datetime.utcnow() >= (self.last_sync_at + timedelta(hours=1))
    
    def update_tokens(self, access_token, refresh_token, expires_in=3600):
        """Update OAuth tokens after refresh."""
        self.access_token = access_token
        self.refresh_token = refresh_token
        self.token_expires_at = datetime.utcnow() + timedelta(seconds=expires_in)
        self.connection_error = None
    
    def mark_synced(self):
        """Update last sync timestamp."""
        self.last_sync_at = datetime.utcnow()
        self.connection_error = None
    
    def mark_error(self, error_message):
        """Record connection error."""
        self.connection_error = error_message
        self.is_active = False
    
    def to_dict(self, include_tokens=False):
        """Serialize to dictionary."""
        data = {
            'id': self.id,
            'user_id': self.user_id,
            'realm_id': self.realm_id,
            'company_name': self.company_name,
            'company_type': self.company_type,
            'is_active': self.is_active,
            'is_sandbox': self.is_sandbox,
            'last_sync_at': self.last_sync_at.isoformat() if self.last_sync_at else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'transaction_count': self.transactions.count(),
            'token_expired': self.is_token_expired
        }
        
        if include_tokens:
            data['access_token'] = self.access_token
            data['refresh_token'] = self.refresh_token
        
        return data
    
    def __repr__(self):
        return f'<Company {self.company_name} ({self.realm_id})>'
