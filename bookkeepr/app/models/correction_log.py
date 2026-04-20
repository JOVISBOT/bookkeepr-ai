"""
Correction Log Model - Store user corrections for AI learning

Phase 2.4: Learning System
Records when users correct AI categorizations to improve future predictions.
"""
from app import db
from datetime import datetime


class CorrectionLog(db.Model):
    """
    Log of user corrections to AI categorizations
    Used for:
    - Training data for AI improvement
    - Accuracy metrics calculation
    - Pattern detection for auto-rule generation
    """
    __tablename__ = 'correction_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    company_id = db.Column(db.Integer, db.ForeignKey('companies.id'), nullable=False, index=True)
    transaction_id = db.Column(db.Integer, db.ForeignKey('transactions.id'), nullable=False, index=True)
    
    # Original AI categorization
    original_account_id = db.Column(db.Integer, db.ForeignKey('accounts.id'))
    original_confidence = db.Column(db.Float, default=0.0)
    
    # User correction
    corrected_account_id = db.Column(db.Integer, db.ForeignKey('accounts.id'), nullable=False)
    
    # Transaction snapshot for pattern analysis
    payee_name = db.Column(db.String(256), index=True)
    description = db.Column(db.Text)
    amount = db.Column(db.Numeric(15, 2))
    transaction_type = db.Column(db.String(50))
    
    # AI details
    ai_confidence = db.Column(db.Float, default=0.0)
    ai_rules_matched = db.Column(db.JSON)  # Rules that matched
    
    # Pattern analysis
    correction_pattern = db.Column(db.String(256))  # e.g., "payee:vendor_name"
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    
    # Relationships
    transaction = db.relationship('Transaction', backref='corrections')
    original_account = db.relationship('Account', foreign_keys=[original_account_id])
    corrected_account = db.relationship('Account', foreign_keys=[corrected_account_id])
    
    @classmethod
    def get_recent(cls, company_id, limit=100):
        """Get recent corrections for a company"""
        return cls.query.filter_by(company_id=company_id)\
            .order_by(cls.created_at.desc())\
            .limit(limit).all()
    
    @classmethod
    def get_common_patterns(cls, user_id, min_count=3):
        """
        Find common correction patterns
        
        Returns patterns that occur frequently enough to auto-generate rules
        """
        from sqlalchemy import func
        
        patterns = db.session.query(
            cls.payee_name,
            cls.corrected_account_id,
            func.count(cls.id).label('count')
        ).filter(
            cls.user_id == user_id,
            cls.payee_name.isnot(None)
        ).group_by(
            cls.payee_name,
            cls.corrected_account_id
        ).having(
            func.count(cls.id) >= min_count
        ).order_by(func.count(cls.id).desc()).all()
        
        return [
            {
                'payee_name': p[0],
                'account_id': p[1],
                'count': p[2]
            }
            for p in patterns
        ]
    
    @classmethod
    def get_accuracy_stats(cls, company_id, days=30):
        """Get correction statistics for accuracy calculation"""
        from datetime import timedelta
        since = datetime.utcnow() - timedelta(days=days)
        
        total = cls.query.filter(
            cls.company_id == company_id,
            cls.created_at >= since
        ).count()
        
        by_confidence = db.session.query(
            cls.ai_confidence,
            db.func.count(cls.id)
        ).filter(
            cls.company_id == company_id,
            cls.created_at >= since
        ).group_by(cls.ai_confidence).all()
        
        return {
            'total_corrections': total,
            'by_confidence': {str(c): n for c, n in by_confidence}
        }
    
    def to_dict(self):
        """Serialize to dict"""
        return {
            'id': self.id,
            'transaction_id': self.transaction_id,
            'original_account_id': self.original_account_id,
            'corrected_account_id': self.corrected_account_id,
            'payee_name': self.payee_name,
            'description': self.description,
            'amount': float(self.amount) if self.amount else None,
            'ai_confidence': self.ai_confidence,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
    
    def __repr__(self):
        return f'<CorrectionLog {self.payee_name} → Account {self.corrected_account_id}>'
