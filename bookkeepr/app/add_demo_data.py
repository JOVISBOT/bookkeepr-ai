"""Add demo transactions for charts"""
import sys
sys.path.insert(0, r'C:\Users\jovis\.openclaw\workspace\bookkeepr\app')

from app import create_app
from app.models import Transaction, Company
from extensions import db
from datetime import datetime, timedelta
import random

app = create_app()

with app.app_context():
    # Get or create company
    company = Company.query.first()
    if not company:
        print("No company found")
        exit()
    
    # Check if we already have transactions
    existing = Transaction.query.filter_by(company_id=company.id).count()
    if existing > 0:
        print(f"Already have {existing} transactions")
        exit()
    
    # Create demo transactions for last 6 months
    categories = ['Sales', 'Services', 'Operating Expenses', 'Equipment', 'Marketing', 'Rent', 'Utilities']
    
    for i in range(50):
        date = datetime.now() - timedelta(days=random.randint(1, 180))
        amount = random.uniform(100, 5000) * random.choice([-1, 1])
        
        txn = Transaction(
            company_id=company.id,
            qbo_transaction_id=f'DEMO-{i:04d}',
            transaction_type='JournalEntry',
            transaction_date=date.date(),
            amount=amount,
            description=f'Transaction {i+1}',
            vendor_name=f'Vendor {random.randint(1, 10)}',
            category=random.choice(categories),
            categorization_status='categorized',
            categorized_by='ai'
        )
        db.session.add(txn)
    
    db.session.commit()
    print("50 demo transactions added!")
