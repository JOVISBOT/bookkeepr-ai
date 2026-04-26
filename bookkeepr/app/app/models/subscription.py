"""Subscription and Billing Models"""
from datetime import datetime
from extensions import db


class SubscriptionPlan(db.Model):
    """Available subscription plans"""
    
    __tablename__ = 'subscription_plans'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)  # starter, pro, business, enterprise
    display_name = db.Column(db.String(100), nullable=False)
    price_monthly = db.Column(db.Numeric(10, 2), nullable=False)
    price_yearly = db.Column(db.Numeric(10, 2), nullable=False)
    
    # Limits
    max_transactions = db.Column(db.Integer, default=1000)  # per month
    max_companies = db.Column(db.Integer, default=1)
    max_users = db.Column(db.Integer, default=1)
    
    # Features
    has_ai_categorization = db.Column(db.Boolean, default=True)
    has_anomaly_detection = db.Column(db.Boolean, default=False)
    has_cashflow_forecasting = db.Column(db.Boolean, default=False)
    has_advanced_reports = db.Column(db.Boolean, default=False)
    has_api_access = db.Column(db.Boolean, default=False)
    has_priority_support = db.Column(db.Boolean, default=False)
    has_dedicated_manager = db.Column(db.Boolean, default=False)
    
    # Stripe
    stripe_price_id_monthly = db.Column(db.String(100))
    stripe_price_id_yearly = db.Column(db.String(100))
    
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'display_name': self.display_name,
            'price_monthly': float(self.price_monthly),
            'price_yearly': float(self.price_yearly),
            'max_transactions': self.max_transactions,
            'max_companies': self.max_companies,
            'max_users': self.max_users,
            'features': {
                'ai_categorization': self.has_ai_categorization,
                'anomaly_detection': self.has_anomaly_detection,
                'cashflow_forecasting': self.has_cashflow_forecasting,
                'advanced_reports': self.has_advanced_reports,
                'api_access': self.has_api_access,
                'priority_support': self.has_priority_support,
                'dedicated_manager': self.has_dedicated_manager,
            }
        }


class UserSubscription(db.Model):
    """User's active subscription"""
    
    __tablename__ = 'user_subscriptions'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, unique=True)
    plan_id = db.Column(db.Integer, db.ForeignKey('subscription_plans.id'), nullable=False)
    
    # Stripe
    stripe_customer_id = db.Column(db.String(100))
    stripe_subscription_id = db.Column(db.String(100))
    stripe_payment_method_id = db.Column(db.String(100))
    
    # Billing
    billing_cycle = db.Column(db.String(20), default='monthly')  # monthly, yearly
    current_period_start = db.Column(db.DateTime)
    current_period_end = db.Column(db.DateTime)
    
    # Status
    status = db.Column(db.String(50), default='trialing')  # trialing, active, past_due, canceled, unpaid
    cancel_at_period_end = db.Column(db.Boolean, default=False)
    
    # Usage tracking
    transactions_used_this_period = db.Column(db.Integer, default=0)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    canceled_at = db.Column(db.DateTime)
    
    # Relationships
    user = db.relationship('User', backref=db.backref('subscription', uselist=False))
    plan = db.relationship('SubscriptionPlan')
    
    @property
    def is_active(self):
        return self.status in ['trialing', 'active']
    
    @property
    def is_trial(self):
        return self.status == 'trialing'
    
    @property
    def days_until_renewal(self):
        if not self.current_period_end:
            return 0
        delta = self.current_period_end - datetime.utcnow()
        return max(0, delta.days)
    
    def to_dict(self):
        return {
            'id': self.id,
            'plan': self.plan.to_dict() if self.plan else None,
            'billing_cycle': self.billing_cycle,
            'status': self.status,
            'is_active': self.is_active,
            'is_trial': self.is_trial,
            'current_period_end': self.current_period_end.isoformat() if self.current_period_end else None,
            'days_until_renewal': self.days_until_renewal,
            'cancel_at_period_end': self.cancel_at_period_end,
            'transactions_used': self.transactions_used_this_period,
        }


class BillingInvoice(db.Model):
    """Invoice history"""
    
    __tablename__ = 'billing_invoices'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    stripe_invoice_id = db.Column(db.String(100), unique=True)
    
    amount = db.Column(db.Numeric(10, 2), nullable=False)
    currency = db.Column(db.String(3), default='usd')
    status = db.Column(db.String(50))  # paid, open, void, uncollectible
    
    period_start = db.Column(db.DateTime)
    period_end = db.Column(db.DateTime)
    paid_at = db.Column(db.DateTime)
    
    pdf_url = db.Column(db.Text)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'amount': float(self.amount),
            'currency': self.currency,
            'status': self.status,
            'period_start': self.period_start.isoformat() if self.period_start else None,
            'period_end': self.period_end.isoformat() if self.period_end else None,
            'paid_at': self.paid_at.isoformat() if self.paid_at else None,
            'pdf_url': self.pdf_url,
        }
