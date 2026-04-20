"""
Test authentication routes
"""
import pytest


class TestAuthRoutes:
    """Test authentication routes."""
    
    def test_login_page(self, client):
        """Test login page loads."""
        response = client.get('/auth/login')
        assert response.status_code == 200
        assert b'Sign in' in response.data
    
    def test_register_page(self, client):
        """Test register page loads."""
        response = client.get('/auth/register')
        assert response.status_code == 200
        assert b'Create your account' in response.data
    
    def test_successful_login(self, client, test_user):
        """Test successful login."""
        response = client.post('/auth/login', data={
            'email': 'test@example.com',
            'password': 'password123'
        }, follow_redirects=True)
        
        assert response.status_code == 200
        assert b'Dashboard' in response.data or b'Welcome' in response.data
    
    def test_failed_login(self, client):
        """Test failed login."""
        response = client.post('/auth/login', data={
            'email': 'wrong@example.com',
            'password': 'wrongpassword'
        }, follow_redirects=True)
        
        assert b'Invalid' in response.data
    
    def test_logout(self, client, test_user):
        """Test logout."""
        # Login first
        client.post('/auth/login', data={
            'email': 'test@example.com',
            'password': 'password123'
        })
        
        # Then logout
        response = client.get('/auth/logout', follow_redirects=True)
        assert response.status_code == 200


class TestRegistration:
    """Test user registration."""
    
    def test_valid_registration(self, client, app):
        """Test valid registration."""
        response = client.post('/auth/register', data={
            'email': 'newuser@example.com',
            'password': 'securepassword123',
            'confirm_password': 'securepassword123',
            'first_name': 'New',
            'last_name': 'User'
        }, follow_redirects=True)
        
        assert response.status_code == 200
        
        # Verify user was created
        with app.app_context():
            from src.models import User
            user = User.query.filter_by(email='newuser@example.com').first()
            assert user is not None
            assert user.first_name == 'New'
    
    def test_registration_password_mismatch(self, client):
        """Test registration with mismatched passwords."""
        response = client.post('/auth/register', data={
            'email': 'test2@example.com',
            'password': 'password123',
            'confirm_password': 'differentpassword'
        }, follow_redirects=True)
        
        assert b'do not match' in response.data
    
    def test_registration_short_password(self, client):
        """Test registration with short password."""
        response = client.post('/auth/register', data={
            'email': 'test3@example.com',
            'password': 'short',
            'confirm_password': 'short'
        }, follow_redirects=True)
        
        assert b'8 characters' in response.data
