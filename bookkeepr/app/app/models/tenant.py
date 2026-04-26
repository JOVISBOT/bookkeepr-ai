"""Tenant Model - Multi-tenant isolation"""
from datetime import datetime
from extensions import db


class Tenant(db.Model):
    """Tenant = isolated workspace for an operator's bookkeeping firm"""
    
    __tablename__ = 'tenants'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # Identity
    name = db.Column(db.String(255), nullable=False)  # "Smith Bookkeeping LLC"
    slug = db.Column(db.String(100), unique=True, nullable=False, index=True)  # "smith-bk"
    subdomain = db.Column(db.String(100), unique=True, index=True)  # "smith-bk.bookkeepr.app"
    
    # Plan
    plan_tier = db.Column(db.String(20), default='starter')  # starter, pro, business, enterprise
    plan_status = db.Column(db.String(20), default='trialing')  # trialing, active, past_due, canceled
    trial_ends_at = db.Column(db.DateTime)
    
    # Limits (per tier)
    max_clients = db.Column(db.Integer, default=1)
    max_transactions_per_month = db.Column(db.Integer, default=1000)
    
    # Branding (white-label)
    logo_url = db.Column(db.String(500))
    primary_color = db.Column(db.String(7), default='#3B82F6')  # hex
    
    # Status
    is_active = db.Column(db.Boolean, default=True)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    users = db.relationship('User', backref='tenant', lazy='dynamic')
    companies = db.relationship('Company', backref='tenant', lazy='dynamic')
    
    def __repr__(self):
        return f'<Tenant {self.name} ({self.slug})>'
    
    @property
    def is_trial_expired(self):
        if self.plan_status != 'trialing':
            return False
        if not self.trial_ends_at:
            return False
        return datetime.utcnow() > self.trial_ends_at
    
    def can_add_client(self):
        """Check if tenant can add another client based on plan"""
        current = self.companies.filter_by(is_active=True).count()
        return current < self.max_clients
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'slug': self.slug,
            'subdomain': self.subdomain,
            'plan_tier': self.plan_tier,
            'plan_status': self.plan_status,
            'max_clients': self.max_clients,
            'is_active': self.is_active,
            'trial_ends_at': self.trial_ends_at.isoformat() if self.trial_ends_at else None,
            'is_trial_expired': self.is_trial_expired,
        }
    
    @classmethod
    def create_for_user(cls, user, name=None):
        """Create a default tenant when a user signs up"""
        from datetime import timedelta
        if not name:
            name = f"{user.full_name or user.email}'s Workspace"
        
        # Generate unique slug
        base_slug = name.lower().replace(' ', '-').replace("'", '')[:50]
        slug = base_slug
        counter = 1
        while cls.query.filter_by(slug=slug).first():
            slug = f"{base_slug}-{counter}"
            counter += 1
        
        # Set tier limits
        tier_limits = {
            'starter': {'max_clients': 1, 'max_transactions_per_month': 1000},
            'pro': {'max_clients': 3, 'max_transactions_per_month': 5000},
            'business': {'max_clients': 10, 'max_transactions_per_month': 25000},
            'enterprise': {'max_clients': 999, 'max_transactions_per_month': 999999},
        }
        limits = tier_limits['starter']
        
        tenant = cls(
            name=name,
            slug=slug,
            plan_tier='starter',
            plan_status='trialing',
            trial_ends_at=datetime.utcnow() + timedelta(days=14),
            **limits,
        )
        db.session.add(tenant)
        db.session.flush()  # get id
        return tenant
