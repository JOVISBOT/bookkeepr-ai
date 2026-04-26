"""Migration: Add multi-tenancy + audit log to BookKeepr
Phase 1.1.3-1.1.6 implementation
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from extensions import db
from sqlalchemy import text, inspect

app = create_app()

def migrate():
    with app.app_context():
        print("=== Migrating BookKeepr to Multi-Tenant ===\n")
        
        # Step 1: Create new tables (tenants, audit_log)
        print("1. Creating new tables (tenants, audit_log)...")
        db.create_all()
        print("   Done")
        
        inspector = inspect(db.engine)
        
        # Step 2: Add columns to existing tables (SQLite limitation - use ALTER TABLE)
        print("\n2. Adding tenant_id and role columns to users table...")
        user_cols = [c['name'] for c in inspector.get_columns('users')]
        
        if 'tenant_id' not in user_cols:
            db.session.execute(text("ALTER TABLE users ADD COLUMN tenant_id INTEGER REFERENCES tenants(id)"))
            print("   Added tenant_id")
        else:
            print("   tenant_id already exists")
        
        if 'role' not in user_cols:
            db.session.execute(text("ALTER TABLE users ADD COLUMN role VARCHAR(20) DEFAULT 'operator' NOT NULL"))
            print("   Added role")
        
        if 'mfa_enabled' not in user_cols:
            db.session.execute(text("ALTER TABLE users ADD COLUMN mfa_enabled BOOLEAN DEFAULT 0"))
            print("   Added mfa_enabled")
        
        if 'mfa_secret' not in user_cols:
            db.session.execute(text("ALTER TABLE users ADD COLUMN mfa_secret VARCHAR(64)"))
            print("   Added mfa_secret")
        
        # Step 3: Add tenant_id to companies
        print("\n3. Adding tenant_id and is_active to companies table...")
        co_cols = [c['name'] for c in inspector.get_columns('companies')]
        
        if 'tenant_id' not in co_cols:
            db.session.execute(text("ALTER TABLE companies ADD COLUMN tenant_id INTEGER REFERENCES tenants(id)"))
            print("   Added tenant_id")
        
        if 'is_active' not in co_cols:
            db.session.execute(text("ALTER TABLE companies ADD COLUMN is_active BOOLEAN DEFAULT 1"))
            print("   Added is_active")
        
        db.session.commit()
        
        # Step 4: Create default tenant for existing users
        print("\n4. Creating tenants for existing users...")
        from app.models import User, Tenant, Company
        
        users_without_tenant = User.query.filter(User.tenant_id == None).all()
        for user in users_without_tenant:
            tenant = Tenant.create_for_user(user)
            user.tenant_id = tenant.id
            user.role = 'operator'  # existing users become operators
            print(f"   Created tenant '{tenant.name}' for {user.email}")
            
            # Update their companies
            user_companies = Company.query.filter_by(user_id=user.id).all()
            for company in user_companies:
                company.tenant_id = tenant.id
        
        db.session.commit()
        
        # Verify
        print("\n5. Verification:")
        print(f"   Total tenants: {Tenant.query.count()}")
        print(f"   Total users: {User.query.count()}")
        print(f"   Users with tenant: {User.query.filter(User.tenant_id != None).count()}")
        print(f"   Total companies: {Company.query.count()}")
        print(f"   Companies with tenant: {Company.query.filter(Company.tenant_id != None).count()}")
        
        print("\nMigration complete!")
        return True

if __name__ == "__main__":
    try:
        migrate()
        sys.exit(0)
    except Exception as e:
        print(f"\nMigration failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
