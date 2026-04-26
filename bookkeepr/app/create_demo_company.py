"""Create demo company"""
import sys
sys.path.insert(0, r'C:\Users\jovis\.openclaw\workspace\bookkeepr\app')

from app import create_app
from app.models import Company, User
from extensions import db

app = create_app()

with app.app_context():
    # Get demo user
    user = User.query.filter_by(email='test@bookkeepr.ai').first()
    if not user:
        print("Demo user not found")
        exit()
    
    # Check if user already has company
    company = Company.query.filter_by(user_id=user.id).first()
    if company:
        print(f"User already has company: {company.qbo_company_name}")
        exit()
    
    # Create demo company
    company = Company(
        user_id=user.id,
        qbo_realm_id='DEMO123',
        qbo_company_name='Demo Company LLC',
        qbo_company_email='demo@company.com',
        is_connected=False,
        sync_status='disconnected'
    )
    db.session.add(company)
    db.session.commit()
    
    print(f"Demo company created: {company.qbo_company_name} (ID: {company.id})")
