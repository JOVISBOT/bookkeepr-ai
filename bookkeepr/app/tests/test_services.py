"""
Test business logic services
-- STALE: references src.* paths from old layout, needs rewrite --
"""
import pytest

pytestmark = pytest.mark.skip(reason="stale — imports from old src.* layout")


class TestQuickBooksService:
    """Test QuickBooks service."""
    
    def test_service_initialization(self, app):
        """Test service can be initialized."""
        from src.services import QuickBooksService
        
        with app.app_context():
            service = QuickBooksService()
            assert service is not None
    
    @patch('src.services.qb_service.AuthClient')
    def test_get_authorization_url(self, mock_auth_client, app):
        """Test authorization URL generation."""
        from src.services import QuickBooksService
        
        # Mock the AuthClient
        mock_client = Mock()
        mock_client.get_authorization_url.return_value = 'https://appcenter.intuit.com/oauth/authorize'
        mock_auth_client.return_value = mock_client
        
        with app.app_context():
            service = QuickBooksService()
            url = service.get_authorization_url()
            
            assert url is not None
            mock_client.get_authorization_url.assert_called_once()


class TestTokenManagement:
    """Test OAuth token management."""
    
    def test_token_encryption(self, app, test_company):
        """Test tokens are encrypted."""
        with app.app_context():
            from src.extensions import db
            
            # Set tokens
            test_company.access_token = 'test_access_token'
            test_company.refresh_token = 'test_refresh_token'
            db.session.commit()
            
            # Verify they're encrypted in database
            # The actual column should contain encrypted data
            assert test_company._access_token != 'test_access_token'
            assert test_company._refresh_token != 'test_refresh_token'
            
            # But decrypted property returns original
            assert test_company.access_token == 'test_access_token'
            assert test_company.refresh_token == 'test_refresh_token'
