"""Seed database with mock data for testing"""
import os
import sys
from datetime import datetime, timedelta
from decimal import Decimal
import random

# Load environment
from dotenv import load_dotenv
load_dotenv()

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app, db
from app.models.user import User
from app.models.company import Company
from app.models.account import Account
from app.models.transaction import Transaction
from app.models.category_rule import CategoryRule

app = create_app('development')

def seed_data():
    with app.app_context():
        print("Creating database tables...")
        db.create_all()
        print("✓ Database tables created\n")
        
        print("Creating mock data...")
        
        # Create user
        user = User.query.filter_by(email='test@bookkeepr.ai').first()
        if not user:
            user = User(
                email='test@bookkeepr.ai',
                first_name='Test',
                last_name='User'
            )
            user.set_password('password123')
            db.session.add(user)
            db.session.commit()
            print(f"✓ Created user: {user.email}")
        else:
            print(f"✓ User exists: {user.email}")
        
        # Create company (use qbo_realm_id as unique field)
        company = Company.query.filter_by(qbo_realm_id='demo_realm_123').first()
        if not company:
            company = Company(
                user_id=user.id,
                qbo_realm_id='demo_realm_123',
                qbo_company_name='Demo Company',
                is_connected=True,
                sync_status='success'
            )
            db.session.add(company)
            db.session.commit()
            print(f"✓ Created company: {company.qbo_company_name}")
        else:
            print(f"✓ Company exists: {company.qbo_company_name}")
        
        # Create accounts (Chart of Accounts)
        accounts_data = [
            ('Office Supplies', 'Expense', 6000),
            ('Software Subscriptions', 'Expense', 6001),
            ('Rent', 'Expense', 6002),
            ('Utilities', 'Expense', 6003),
            ('Marketing', 'Expense', 6004),
            ('Travel', 'Expense', 6005),
            ('Meals & Entertainment', 'Expense', 6006),
            ('Professional Services', 'Expense', 6007),
            ('Sales Revenue', 'Income', 4000),
            ('Consulting Revenue', 'Income', 4001),
            ('Checking Account', 'Asset', 1000),
            ('Savings Account', 'Asset', 1001),
        ]
        
        accounts = {}
        for name, acc_type, qbo_id in accounts_data:
            acc = Account.query.filter_by(
                company_id=company.id, 
                qbo_account_id=str(qbo_id)
            ).first()
            if not acc:
                acc = Account(
                    company_id=company.id,
                    qbo_account_id=str(qbo_id),
                    name=name,
                    account_type=acc_type,
                    classification=acc_type,
                    is_active=True
                )
                db.session.add(acc)
                db.session.commit()
                accounts[name] = acc
                print(f"  + Created account: {name}")
            else:
                accounts[name] = acc
        print(f"✓ Created {len(accounts)} accounts\n")
        
        # Create category rules
        rules_data = [
            ('Amazon Rule', 'Amazon', 'Office Supplies'),
            ('AWS Rule', 'AWS', 'Software Subscriptions'),
            ('Stripe Rule', 'Stripe', 'Sales Revenue'),
            ('Uber Rule', 'Uber', 'Travel'),
            ('Starbucks Rule', 'Starbucks', 'Meals & Entertainment'),
        ]
        
        for rule_name, vendor, account_name in rules_data:
            if account_name in accounts:
                rule = CategoryRule.query.filter_by(
                    company_id=company.id,
                    vendor_name=vendor
                ).first()
                if not rule:
                    rule = CategoryRule(
                        user_id=user.id,
                        company_id=company.id,
                        name=rule_name,
                        rule_type='vendor',
                        vendor_name=vendor,
                        target_account_id=accounts[account_name].id,
                        priority=100
                    )
                    db.session.add(rule)
        db.session.commit()
        print(f"✓ Created {len(rules_data)} category rules\n")
        
        # Create transactions
        vendors = {
            'Office Supplies': ['Amazon', 'Staples', 'Office Depot'],
            'Software Subscriptions': ['AWS', 'GitHub', 'Slack', 'Notion'],
            'Rent': ['WeWork', 'Regus', 'Landlord LLC'],
            'Utilities': ['PG&E', 'Comcast', 'Verizon'],
            'Marketing': ['Google Ads', 'Facebook Ads', 'LinkedIn Ads'],
            'Travel': ['Uber', 'Lyft', 'United Airlines', 'Marriott'],
            'Meals & Entertainment': ['Starbucks', 'DoorDash', 'Chipotle'],
            'Professional Services': ['Upwork', 'Fiverr', 'LegalZoom'],
        }
        
        # Generate 50 expense transactions over last 3 months
        transaction_count = 0
        for i in range(50):
            days_ago = random.randint(1, 90)
            tx_date = datetime.now() - timedelta(days=days_ago)
            
            category = random.choice(list(vendors.keys()))
            vendor = random.choice(vendors[category])
            account = accounts[category]
            
            # Amount based on category
            if category == 'Rent':
                amount = Decimal(random.randint(2000, 5000))
            elif category == 'Software Subscriptions':
                amount = Decimal(random.randint(50, 500))
            elif category == 'Marketing':
                amount = Decimal(random.randint(100, 2000))
            else:
                amount = Decimal(random.randint(20, 500))
            
            confidence = random.choice([0.92, 0.85, 0.78, 0.65])
            needs_review = confidence < 0.85
            
            tx = Transaction(
                company_id=company.id,
                account_id=account.id,
                qbo_transaction_id=f'txn_{i+1000}',
                transaction_type='Purchase',
                transaction_date=tx_date.date(),
                amount=amount,
                description=f'{vendor} - {tx_date.strftime("%b %Y")}',
                vendor_name=vendor,
                account_name=account.name,
                category=account.name,
                categorization_status='categorized' if not needs_review else 'suggested',
                suggested_category=account.name,
                suggested_confidence=confidence * 100,
                categorized_by='ai',
                review_status='approved' if not needs_review else 'pending',
                created_at=tx_date
            )
            db.session.add(tx)
            transaction_count += 1
        
        # Add revenue transactions
        for i in range(10):
            days_ago = random.randint(1, 90)
            tx_date = datetime.now() - timedelta(days=days_ago)
            amount = Decimal(random.randint(1000, 10000))
            
            tx = Transaction(
                company_id=company.id,
                account_id=accounts['Consulting Revenue'].id,
                qbo_transaction_id=f'txn_rev_{i+2000}',
                transaction_type='Deposit',
                transaction_date=tx_date.date(),
                amount=amount,
                description=f'Consulting - {tx_date.strftime("%b %Y")}',
                vendor_name='Client Payment',
                account_name='Consulting Revenue',
                category='Consulting Revenue',
                categorization_status='categorized',
                suggested_category='Consulting Revenue',
                suggested_confidence=95,
                categorized_by='ai',
                review_status='approved',
                created_at=tx_date
            )
            db.session.add(tx)
            transaction_count += 1
        
        db.session.commit()
        print(f"✓ Created {transaction_count} transactions\n")
        
        print("=" * 50)
        print("✅ MOCK DATA CREATED SUCCESSFULLY!")
        print("=" * 50)
        print(f"\nLogin credentials:")
        print(f"  Email: test@bookkeepr.ai")
        print(f"  Password: password123")
        print(f"\nSummary:")
        print(f"  • User: {user.email}")
        print(f"  • Company: {company.qbo_company_name}")
        print(f"  • Accounts: {len(accounts)}")
        print(f"  • Transactions: {transaction_count}")
        print(f"\nDashboard should now show data!")

if __name__ == '__main__':
    seed_data()
