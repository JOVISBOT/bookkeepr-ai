"""
User model for application authentication
"""
from datetime import datetime
from flask_login import UserMixin
from ..extensions import db, bcrypt


class User(UserMixin, db.Model):
    """
    User model for business owners/accountants.
    One user can have multiple connected companies.
    """
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    first_name = db.Column(db.String(100))
    last_name = db.Column(db.String(100))
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    is_admin = db.Column(db.Boolean, default=False, nullable=False)
    email_verified = db.Column(db.Boolean, default=False, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, 
                          onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    companies = db.relationship('Company', backref='user', lazy='dynamic',
                               cascade='all, delete-orphan')
    
    def __init__(self, email, password, first_name=None, last_name=None):
        self.email = email.lower().strip()
        self.password_hash = bcrypt.generate_password_hash(password).decode('utf-8')
        self.first_name = first_name
        self.last_name = last_name
    
    def check_password(self, password):
        """Verify password against hash."""
        return bcrypt.check_password_hash(self.password_hash, password)
    
    def set_password(self, password):
        """Set new password."""
        self.password_hash = bcrypt.generate_password_hash(password).decode('utf-8')
    
    @property
    def full_name(self):
        """Return full name."""
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}"
        return self.first_name or self.last_name or self.email
    
    def to_dict(self):
        """Serialize to dictionary."""
        return {
            'id': self.id,
            'email': self.email,
            'first_name': self.first_name,
            'last_name': self.last_name,
            'full_name': self.full_name,
            'is_active': self.is_active,
            'is_admin': self.is_admin,
            'email_verified': self.email_verified,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'company_count': self.companies.count()
        }
    
    def __repr__(self):
        return f'<User {self.email}>'


# Flask-Login user loader
from ..extensions import login_manager

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))
