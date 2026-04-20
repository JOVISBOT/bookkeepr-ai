"""Category Rule Model - Auto-categorization rules"""
from app import db
from datetime import datetime


class CategoryRule(db.Model):
    """User-defined rules for auto-categorizing transactions"""
    __tablename__ = 'category_rules'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    company_id = db.Column(db.Integer, db.ForeignKey('companies.id'), nullable=False, index=True)
    
    # Rule details
    name = db.Column(db.String(256), nullable=False)
    rule_type = db.Column(db.String(50), default='keyword')  # keyword, vendor, amount_range
    
    # Matching criteria
    keyword = db.Column(db.String(256))
    vendor_name = db.Column(db.String(256), index=True)
    min_amount = db.Column(db.Numeric(15, 2))
    max_amount = db.Column(db.Numeric(15, 2))
    
    # Target category
    target_account_id = db.Column(db.Integer, db.ForeignKey('accounts.id'), nullable=False)
    
    # Rule behavior
    priority = db.Column(db.Integer, default=100)  # Lower = higher priority
    active = db.Column(db.Boolean, default=True)
    auto_apply = db.Column(db.Boolean, default=True)  # Apply without review?
    
    # Statistics
    match_count = db.Column(db.Integer, default=0)
    last_matched_at = db.Column(db.DateTime)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = db.relationship('User', backref='category_rules')
    company = db.relationship('Company', backref='category_rules')
    target_account = db.relationship('Account', foreign_keys=[target_account_id])
    
    def matches_transaction(self, transaction):
        """Check if this rule matches a transaction"""
        if not self.active:
            return False
        
        # Check vendor name match
        if self.vendor_name and transaction.payee_name:
            if self.vendor_name.lower() in transaction.payee_name.lower():
                return True
        
        # Check keyword in description
        if self.keyword and transaction.description:
            if self.keyword.lower() in transaction.description.lower():
                return True
        
        # Check amount range
        if transaction.amount is not None:
            if self.min_amount is not None:
                if transaction.amount < self.min_amount:
                    return False
            if self.max_amount is not None:
                if transaction.amount > self.max_amount:
                    return False
            # If only amount criteria specified and passed
            if self.min_amount is not None or self.max_amount is not None:
                if not self.vendor_name and not self.keyword:
                    return True
        
        return False
    
    def record_match(self):
        """Record that this rule matched a transaction"""
        self.match_count += 1
        self.last_matched_at = datetime.utcnow()
    
    @classmethod
    def get_active_rules(cls, user_id, company_id):
        """Get all active rules for a user/company"""
        return cls.query.filter_by(
            user_id=user_id,
            company_id=company_id,
            active=True
        ).order_by(cls.priority.asc()).all()
    
    def to_dict(self):
        """Serialize to dict"""
        return {
            'id': self.id,
            'name': self.name,
            'rule_type': self.rule_type,
            'keyword': self.keyword,
            'vendor_name': self.vendor_name,
            'min_amount': float(self.min_amount) if self.min_amount else None,
            'max_amount': float(self.max_amount) if self.max_amount else None,
            'target_account_id': self.target_account_id,
            'priority': self.priority,
            'active': self.active,
            'auto_apply': self.auto_apply,
            'match_count': self.match_count,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
