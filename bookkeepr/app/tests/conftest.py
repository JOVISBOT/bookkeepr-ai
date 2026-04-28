"""Pytest configuration"""
import sys
import os

collect_ignore = [
    "test_services.py",        # stale — imports from old src.* layout
    "test_ai_categorization.py",  # stale — written for old ML interface
]

# Ensure bookkeepr/app/ is on sys.path so 'from app import create_app' resolves
# to bookkeepr/app/app/__init__.py (the Flask app), not the guard wrapper.
_app_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _app_root not in sys.path:
    sys.path.insert(0, _app_root)

import pytest
from app import create_app
from extensions import db


@pytest.fixture
def app():
    """Create application for testing"""
    app = create_app('testing')

    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    """Test client"""
    return app.test_client()


@pytest.fixture
def runner(app):
    """Test CLI runner"""
    return app.test_cli_runner()


@pytest.fixture
def test_user(app):
    """A registered, active user for login tests"""
    from app.models.user import User
    from app.models.tenant import Tenant

    tenant = Tenant(name='Test Tenant', slug='test-tenant', plan_tier='starter')
    db.session.add(tenant)
    db.session.flush()

    user = User(
        email='test@example.com',
        first_name='Test',
        last_name='User',
        role='operator',
        tenant_id=tenant.id,
        is_active=True,
    )
    user.set_password('password123')
    db.session.add(user)
    db.session.commit()
    yield user
