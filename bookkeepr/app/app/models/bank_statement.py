"""Bank Statement Models for Reconciliation"""
from datetime import datetime
from app import db


class BankStatement(db.Model):
    """Bank statement upload record"""
    __tablename__ = 'bank_statements'
    
    id = db.Column(db.Integer, primary_key=True)
    company_id = db.Column(db.Integer, db.ForeignKey('companies.id'), nullable=False)
    file_name = db.Column(db.String(255), nullable=False)
    file_path = db.Column(db.String(500))
    upload_date = db.Column(db.DateTime, default=datetime.utcnow)
    statement_date = db.Column(db.Date)
    start_balance = db.Column(db.Numeric(12, 2), default=0)
    end_balance = db.Column(db.Numeric(12, 2), default=0)
    status = db.Column(db.String(20), default='pending')  # pending, processing, reconciled
    
    # Relationships
    company = db.relationship('Company', backref='bank_statements')
    lines = db.relationship('BankStatementLine', backref='statement', 
                           lazy='dynamic', cascade='all, delete-orphan')
    
    def to_dict(self):
        return {
            'id': self.id,
            'company_id': self.company_id,
            'file_name': self.file_name,
            'upload_date': self.upload_date.isoformat() if self.upload_date else None,
            'statement_date': self.statement_date.isoformat() if self.statement_date else None,
            'start_balance': str(self.start_balance),
            'end_balance': str(self.end_balance),
            'status': self.status,
            'line_count': self.lines.count()
        }


class BankStatementLine(db.Model):
    """Individual line items from bank statement"""
    __tablename__ = 'bank_statement_lines'
    
    id = db.Column(db.Integer, primary_key=True)
    statement_id = db.Column(db.Integer, db.ForeignKey('bank_statements.id'), nullable=False)
    
    # Transaction data
    line_date = db.Column(db.Date, nullable=False)
    description = db.Column(db.String(500))
    amount = db.Column(db.Numeric(12, 2), nullable=False)
    reference_number = db.Column(db.String(100))
    
    # Matching
    matched_transaction_id = db.Column(db.Integer, db.ForeignKey('transactions.id'))
    match_confidence = db.Column(db.Float, default=0)  # 0-1 score
    match_status = db.Column(db.String(20), default='unmatched')  # unmatched, matched, approved, rejected
    matched_at = db.Column(db.DateTime)
    
    # Relationships
    matched_transaction = db.relationship('Transaction', backref='bank_matches')
    
    def to_dict(self):
        return {
            'id': self.id,
            'statement_id': self.statement_id,
            'line_date': self.line_date.isoformat() if self.line_date else None,
            'description': self.description,
            'amount': str(self.amount),
            'reference_number': self.reference_number,
            'matched_transaction_id': self.matched_transaction_id,
            'match_confidence': self.match_confidence,
            'match_status': self.match_status,
            'matched_at': self.matched_at.isoformat() if self.matched_at else None
        }


class ReconciliationMatch(db.Model):
    """Tracks proposed matches between bank lines and transactions"""
    __tablename__ = 'reconciliation_matches'
    
    id = db.Column(db.Integer, primary_key=True)
    company_id = db.Column(db.Integer, db.ForeignKey('companies.id'), nullable=False)
    
    # The two items being matched
    bank_line_id = db.Column(db.Integer, db.ForeignKey('bank_statement_lines.id'), nullable=False)
    transaction_id = db.Column(db.Integer, db.ForeignKey('transactions.id'), nullable=False)
    
    # Match metadata
    confidence = db.Column(db.Float, nullable=False)  # 0-1
    is_auto_matched = db.Column(db.Boolean, default=False)
    status = db.Column(db.String(20), default='pending')  # pending, approved, rejected
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    approved_at = db.Column(db.DateTime)
    approved_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    
    # Relationships
    company = db.relationship('Company', backref='reconciliation_matches')
    bank_line = db.relationship('BankStatementLine', backref='proposed_matches')
    transaction = db.relationship('Transaction', backref='proposed_matches')
    
    def to_dict(self):
        return {
            'id': self.id,
            'company_id': self.company_id,
            'bank_line_id': self.bank_line_id,
            'transaction_id': self.transaction_id,
            'confidence': self.confidence,
            'is_auto_matched': self.is_auto_matched,
            'status': self.status,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'approved_at': self.approved_at.isoformat() if self.approved_at else None
        }
