"""
Category Rule Model - User-defined and AI-learned rules
"""
from app import db
from datetime import datetime


class CategoryRule(db.Model):
    """
    Rules for auto-categorizing transactions
    Can be user-defined or AI-learned
    """
    __tablename__ = 'category_rules'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    company_id = db.Column(db.Integer, db.ForeignKey('companies.id'), nullable=True, index=True)
    
    # Rule Configuration
    name = db.Column(db.String(256), nullable=False)
    rule_type = db.Column(db.String(50), default='keyword')  # keyword, regex, amount_range, vendor
    
    # Conditions
    keyword = db.Column(db.String(256), index=True)  # For keyword matching
    regex_pattern = db.Column(db.Text)  # For advanced matching
    min_amount = db.Column(db.Numeric(15, 2))
    max_amount = db.Column(db.Numeric(15, 2))
    vendor_name = db.Column(db.String(256), index=True)
    
    # Action
    target_account_id = db.Column(db.Integer, db.ForeignKey('accounts.id'), nullable=False)
    confidence_boost = db.Column(db.Float, default=0.1)  # Add to AI confidence
    
    # Priority (higher = evaluated first)
    priority = db.Column(db.Integer, default=100)
    
    # Status
    is_active = db.Column(db.Boolean, default=True, index=True)
    is_ai_learned = db.Column(db.Boolean, default=False)  # True if AI created it
    
    # Performance tracking
    match_count = db.Column(db.Integer, default=0)
    correction_count = db.Column(db.Integer, default=0)  # User corrected this rule
    last_matched_at = db.Column(db.DateTime)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    target_account = db.relationship('Account', backref='category_rules')
    
    def matches_transaction(self, transaction):
        """Check if this rule matches a transaction"""
        if not self.is_active:
            return False
        
        # Keyword matching
        if self.keyword and self.keyword.lower() in (transaction.description or '').lower():
            return True
        
        # Vendor matching
        if self.vendor_name and self.vendor_name.lower() == (transaction.payee_name or '').lower():
            return True
        
        # Amount range matching
        if self.min_amount is not None and transaction.amount < self.min_amount:
            return False
        if self.max_amount is not None and transaction.amount > self.max_amount:
            return False
        
        # Regex matching
        if self.regex_pattern:
            import re
            if re.search(self.regex_pattern, transaction.description or '', re.IGNORECASE):
                return True
        
        return False
    
    def record_match(self):
        """Record that this rule matched a transaction"""
        self.match_count += 1
        self.last_matched_at = datetime.utcnow()
    
    def record_correction(self):
        """Record that user corrected this rule's categorization"""
        self.correction_count += 1
        if self.correction_count > 5 and self.is_ai_learned:
            # Disable AI-learned rules with too many corrections
            self.is_active = False
    
    @classmethod
    def get_active_rules(cls, user_id, company_id=None):
        """Get active rules ordered by priority"""
        query = cls.query.filter_by(user_id=user_id, is_active=True)
        if company_id:
            query = query.filter(
                (cls.company_id == company_id) | (cls.company_id.is_(None))
            )
        return query.order_by(cls.priority.desc()).all()
    
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
            'is_active': self.is_active,
            'is_ai_learned': self.is_ai_learned,
            'match_count': self.match_count,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
    
    def __repr__(self):
        return f'<CategoryRule {self.name}>'