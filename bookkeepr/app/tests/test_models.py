"""Tests for database models"""
import pytest
from datetime import datetime, timedelta
from app.models.user import User
from app.models.company import Company
from app.models.account import Account
from app.models.transaction import Transaction


class TestUserModel:
    """Test User model"""
    
    def test_user_creation(self, app):
        """Test user creation"""
        with app.app_context():
            user = User(
                email='test@example.com',
                first_name='Test',
                last_name='User'
            )
            assert user.email == 'test@example.com'
            assert user.full_name == 'Test User'
    
    def test_user_to_dict(self, app):
        """Test user serialization"""
        with app.app_context():
            user = User(
                email='test@example.com',
                first_name='Test',
                last_name='User',
                is_active=True
            )
            data = user.to_dict()
            assert data['email'] == 'test@example.com'
            assert data['full_name'] == 'Test User'


class TestCompanyModel:
    """Test Company model"""
    
    def test_company_creation(self, app):
        """Test company creation"""
        with app.app_context():
            company = Company(
                qbo_realm_id='12345',
                qbo_company_name='Test Company'
            )
            assert company.qbo_realm_id == '12345'
            assert company.qbo_company_name == 'Test Company'
    
    def test_token_expiry(self, app):
        """Test token expiry check"""
        with app.app_context():
            # Expired token
            company = Company(
                token_expires_at=datetime.utcnow() - timedelta(hours=1)
            )
            assert company.is_token_expired is True
            
            # Valid token
            company.token_expires_at = datetime.utcnow() + timedelta(hours=1)
            assert company.is_token_expired is False


class TestTransactionModel:
    """Test Transaction model"""
    
    def test_transaction_creation(self, app):
        """Test transaction creation"""
        with app.app_context():
            txn = Transaction(
                qbo_transaction_id='txn_123',
                transaction_type='Purchase',
                amount=-100.00,
                description='Test transaction'
            )
            assert txn.qbo_transaction_id == 'txn_123'
            assert txn.is_expense is True
