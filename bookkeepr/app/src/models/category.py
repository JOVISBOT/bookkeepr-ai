"""
Category model for AI learning and transaction categorization
"""
from datetime import datetime
from ..extensions import db


class Category(db.Model):
    """
    Category model for AI learning.
    Stores custom categories per company with keyword patterns.
    """
    __tablename__ = 'categories'
    
    id = db.Column(db.Integer, primary_key=True)
    company_id = db.Column(db.Integer, db.ForeignKey('companies.id'), 
                          nullable=False, index=True)
    
    # Category info
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    
    # QuickBooks mapping
    account_id = db.Column(db.String(100))  # QBO Chart of Accounts ID
    account_name = db.Column(db.String(255))  # QBO account name
    account_type = db.Column(db.String(50))  # Expense, COGS, etc.
    
    # AI learning - keywords that map to this category
    keywords = db.Column(db.JSON, default=list)  # ["amazon", "aws", "cloud services"]
    
    # Vendor patterns
    vendor_patterns = db.Column(db.JSON, default=list)  # Regex patterns for vendors
    
    # Description patterns
    description_patterns = db.Column(db.JSON, default=list)  # Keywords in descriptions
    
    # Usage stats
    use_count = db.Column(db.Integer, default=0)  # How many times used
    last_used_at = db.Column(db.DateTime)
    
    # Flags
    is_default = db.Column(db.Boolean, default=False)  # System default category
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, 
                          onupdate=datetime.utcnow, nullable=False)
    
    # Unique constraint
    __table_args__ = (
        db.UniqueConstraint('company_id', 'name', name='uix_company_category_name'),
    )
    
    def add_keyword(self, keyword):
        """Add a keyword to this category."""
        if not self.keywords:
            self.keywords = []
        keyword = keyword.lower().strip()
        if keyword not in self.keywords:
            self.keywords.append(keyword)
            self.updated_at = datetime.utcnow()
    
    def remove_keyword(self, keyword):
        """Remove a keyword from this category."""
        if self.keywords:
            keyword = keyword.lower().strip()
            self.keywords = [k for k in self.keywords if k != keyword]
            self.updated_at = datetime.utcnow()
    
    def matches_vendor(self, vendor_name):
        """Check if vendor matches this category's patterns."""
        if not vendor_name or not self.vendor_patterns:
            return False
        vendor_lower = vendor_name.lower()
        for pattern in self.vendor_patterns:
            if pattern.lower() in vendor_lower:
                return True
        return False
    
    def matches_description(self, description):
        """Check if description matches this category's patterns."""
        if not description or not self.description_patterns:
            return False
        desc_lower = description.lower()
        for pattern in self.description_patterns:
            if pattern.lower() in desc_lower:
                return True
        return False
    
    def increment_usage(self):
        """Increment usage count."""
        self.use_count = (self.use_count or 0) + 1
        self.last_used_at = datetime.utcnow()
    
    def to_dict(self):
        """Serialize to dictionary."""
        return {
            'id': self.id,
            'company_id': self.company_id,
            'name': self.name,
            'description': self.description,
            'account_id': self.account_id,
            'account_name': self.account_name,
            'account_type': self.account_type,
            'keywords': self.keywords or [],
            'vendor_patterns': self.vendor_patterns or [],
            'description_patterns': self.description_patterns or [],
            'use_count': self.use_count or 0,
            'is_default': self.is_default,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'last_used_at': self.last_used_at.isoformat() if self.last_used_at else None,
        }
    
    @staticmethod
    def get_default_categories():
        """Return list of default bookkeeping categories."""
        return [
            {'name': 'Advertising & Marketing', 'account_type': 'Expense'},
            {'name': 'Auto & Transport', 'account_type': 'Expense'},
            {'name': 'Bank & Credit Card Fees', 'account_type': 'Expense'},
            {'name': 'Computer & Internet', 'account_type': 'Expense'},
            {'name': 'Contractors', 'account_type': 'Expense'},
            {'name': 'Cost of Goods Sold', 'account_type': 'COGS'},
            {'name': 'Depreciation', 'account_type': 'Expense'},
            {'name': 'Employee Benefits', 'account_type': 'Expense'},
            {'name': 'Entertainment & Meals', 'account_type': 'Expense'},
            {'name': 'Insurance', 'account_type': 'Expense'},
            {'name': 'Interest Paid', 'account_type': 'Expense'},
            {'name': 'Legal & Professional', 'account_type': 'Expense'},
            {'name': 'Office Expenses', 'account_type': 'Expense'},
            {'name': 'Payroll Expenses', 'account_type': 'Expense'},
            {'name': 'Rent or Lease', 'account_type': 'Expense'},
            {'name': 'Repairs & Maintenance', 'account_type': 'Expense'},
            {'name': 'Shipping & Postage', 'account_type': 'Expense'},
            {'name': 'Software & Subscriptions', 'account_type': 'Expense'},
            {'name': 'Supplies', 'account_type': 'Expense'},
            {'name': 'Taxes & Licenses', 'account_type': 'Expense'},
            {'name': 'Telephone & Communications', 'account_type': 'Expense'},
            {'name': 'Travel', 'account_type': 'Expense'},
            {'name': 'Utilities', 'account_type': 'Expense'},
            {'name': 'Equipment', 'account_type': 'Fixed Asset'},
            {'name': 'Uncategorized', 'account_type': 'Expense'},
        ]
    
    def __repr__(self):
        return f'<Category {self.name}>'
