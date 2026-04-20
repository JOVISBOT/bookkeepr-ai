"""
User Model
"""
from app import db, login_manager
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import secrets


class User(UserMixin, db.Model):
    """
    User model for authentication and profile
    """
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(256))
    first_name = db.Column(db.String(64))
    last_name = db.Column(db.String(64))
    
    # Profile
    timezone = db.Column(db.String(64), default='America/Los_Angeles')
    phone = db.Column(db.String(20))
    
    # Subscription
    subscription_tier = db.Column(db.String(20), default='free')  # free, standard, silver, gold
    subscription_status = db.Column(db.String(20), default='inactive')  # inactive, active, past_due, cancelled
    stripe_customer_id = db.Column(db.String(128))
    stripe_subscription_id = db.Column(db.String(128))
    trial_ends_at = db.Column(db.DateTime)
    
    # Status
    is_active = db.Column(db.Boolean, default=True)
    is_admin = db.Column(db.Boolean, default=False)
    email_verified = db.Column(db.Boolean, default=False)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_login_at = db.Column(db.DateTime)
    
    # API
    api_key = db.Column(db.String(128), unique=True, index=True)
    
    # Relationships
    companies = db.relationship('Company', backref='owner', lazy='dynamic', cascade='all, delete-orphan')
    category_rules = db.relationship('CategoryRule', backref='created_by', lazy='dynamic')
    
    def set_password(self, password):
        """Hash and store password"""
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        """Verify password"""
        return check_password_hash(self.password_hash, password)
    
    def generate_api_key(self):
        """Generate unique API key"""
        self.api_key = secrets.token_urlsafe(32)
        return self.api_key
    
    @property
    def full_name(self):
        """Return full name"""
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}"
        return self.email
    
    @property
    def is_trial_active(self):
        """Check if trial is active"""
        if not self.trial_ends_at:
            return False
        return datetime.utcnow() < self.trial_ends_at
    
    @property
    def can_add_company(self):
        """Check if user can add another company"""
        tier_limits = {
            'free': 0,
            'standard': 1,
            'silver': 3,
            'gold': 999  # Unlimited
        }
        limit = tier_limits.get(self.subscription_tier, 0)
        return self.companies.count() < limit
    
    @property
    def transaction_limit(self):
        """Get monthly transaction limit"""
        limits = {
            'free': 0,
            'standard': 500,
            'silver': 2000,
            'gold': 999999  # Unlimited
        }
        return limits.get(self.subscription_tier, 0)
    
    def __repr__(self):
        return f'<User {self.email}>'


@login_manager.user_loader
def load_user(user_id):
    """Load user by ID for Flask-Login"""
    return User.query.get(int(user_id))