"""Subscription model for Stripe billing"""
from datetime import datetime
from app.extensions import db


class Subscription(db.Model):
    """User subscription tracking"""
    __tablename__ = 'subscriptions'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    stripe_customer_id = db.Column(db.String(255), nullable=True)
    stripe_subscription_id = db.Column(db.String(255), nullable=True)
    stripe_price_id = db.Column(db.String(255), nullable=True)
    
    # Plan details
    plan_type = db.Column(db.String(50), default='standard')  # standard, silver, gold
    status = db.Column(db.String(50), default='inactive')  # active, canceled, past_due, etc.
    
    # Billing period
    current_period_start = db.Column(db.DateTime, nullable=True)
    current_period_end = db.Column(db.DateTime, nullable=True)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = db.relationship('User', backref=db.backref('subscription', uselist=False))
    
    def is_active(self):
        """Check if subscription is currently active"""
        return self.status in ['active', 'trialing']
    
    def to_dict(self):
        return {
            'id': self.id,
            'plan_type': self.plan_type,
            'status': self.status,
            'current_period_start': self.current_period_start.isoformat() if self.current_period_start else None,
            'current_period_end': self.current_period_end.isoformat() if self.current_period_end else None,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
