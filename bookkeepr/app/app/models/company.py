"""Company Model"""
from datetime import datetime, timedelta
from extensions import db


def _fernet():
    """Return a Fernet instance using the app's configured key, or None if not set."""
    import os
    key = os.environ.get('FERNET_KEY')
    if not key:
        return None
    try:
        from cryptography.fernet import Fernet
        return Fernet(key.encode() if isinstance(key, str) else key)
    except Exception:
        return None


def _encrypt(value: str | None) -> str | None:
    if not value:
        return value
    f = _fernet()
    return f.encrypt(value.encode()).decode() if f else value


def _decrypt(value: str | None) -> str | None:
    if not value:
        return value
    f = _fernet()
    if not f:
        return value
    try:
        return f.decrypt(value.encode()).decode()
    except Exception:
        return value  # already plaintext (pre-encryption records)


class Company(db.Model):
    """QuickBooks-connected company"""
    
    __tablename__ = 'companies'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    
    # Multi-tenant isolation
    tenant_id = db.Column(db.Integer, db.ForeignKey('tenants.id'), nullable=True, index=True)
    
    # Active/inactive (soft delete)
    is_active = db.Column(db.Boolean, default=True, index=True)
    
    # QuickBooks Info
    qbo_realm_id = db.Column(db.String(50), unique=True, nullable=False, index=True)
    qbo_company_name = db.Column(db.String(255))
    qbo_company_address = db.Column(db.Text)
    qbo_company_email = db.Column(db.String(255))
    qbo_company_phone = db.Column(db.String(50))
    
    # OAuth Tokens (Fernet-encrypted at rest)
    _access_token = db.Column('access_token', db.Text)
    _refresh_token = db.Column('refresh_token', db.Text)
    token_expires_at = db.Column(db.DateTime)

    @property
    def access_token(self):
        return _decrypt(self._access_token)

    @access_token.setter
    def access_token(self, value):
        self._access_token = _encrypt(value)

    @property
    def refresh_token(self):
        return _decrypt(self._refresh_token)

    @refresh_token.setter
    def refresh_token(self, value):
        self._refresh_token = _encrypt(value)
    
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
    
    # Client portal access — operator links a client user to this company
    client_user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True, index=True)

    # Relationships
    accounts = db.relationship('Account', backref='company', lazy='dynamic', cascade='all, delete-orphan')
    transactions = db.relationship('Transaction', backref='company', lazy='dynamic', cascade='all, delete-orphan')
    client_user = db.relationship('User', foreign_keys=[client_user_id], backref='client_companies')
    
    def __repr__(self):
        return f'<Company {self.qbo_company_name or self.qbo_realm_id}>'
    
    @property
    def is_token_expired(self):
        """Check if access token is expired"""
        if not self.token_expires_at:
            return True
        return datetime.utcnow() >= self.token_expires_at

    def needs_token_refresh(self):
        """Return True if token expires within 5 minutes"""
        if not self.token_expires_at:
            return bool(self.refresh_token)
        return datetime.utcnow() >= (self.token_expires_at - timedelta(minutes=5))
    
    @property
    def name(self):
        """Friendly name alias"""
        return self.qbo_company_name or self.qbo_realm_id or f'Company {self.id}'

    def to_dict(self):
        """Serialize to dictionary"""
        return {
            'id': self.id,
            'name': self.name,
            'qbo_realm_id': self.qbo_realm_id,
            'qbo_company_name': self.qbo_company_name,
            'is_connected': self.is_connected,
            'last_sync_at': self.last_sync_at.isoformat() if self.last_sync_at else None,
            'sync_status': self.sync_status,
            'client_user_id': self.client_user_id,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
