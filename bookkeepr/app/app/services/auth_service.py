"""Authentication Service"""
from datetime import datetime, timedelta
from flask import current_app
from intuitlib.client import AuthClient
from intuitlib.enums import Scopes


class AuthService:
    """Handle QuickBooks OAuth authentication"""
    
    def __init__(self):
        self.auth_client = None
        
    def _get_auth_client(self):
        """Initialize Intuit Auth Client"""
        if not self.auth_client:
            self.auth_client = AuthClient(
                client_id=current_app.config['INTUIT_CLIENT_ID'],
                client_secret=current_app.config['INTUIT_CLIENT_SECRET'],
                environment='sandbox' if current_app.config['INTUIT_SANDBOX_MODE'] else 'production',
                redirect_uri=current_app.config['INTUIT_REDIRECT_URI']
            )
        return self.auth_client
    
    def get_authorization_url(self, state=None):
        """Generate OAuth authorization URL"""
        auth_client = self._get_auth_client()
        
        # Parse scopes from config
        scopes = current_app.config['INTUIT_SCOPES'].split()
        
        # Build authorization URL
        auth_url = auth_client.get_authorization_url(scopes)
        
        return auth_url
    
    def exchange_code_for_tokens(self, auth_code, realm_id):
        """Exchange authorization code for access/refresh tokens"""
        auth_client = self._get_auth_client()
        
        try:
            auth_client.get_bearer_token(auth_code, realm_id=realm_id)
            
            return {
                'access_token': auth_client.access_token,
                'refresh_token': auth_client.refresh_token,
                'expires_in': auth_client.expires_in,
                'realm_id': realm_id,
                'token_type': auth_client.token_type
            }
        except Exception as e:
            current_app.logger.error(f"Token exchange failed: {str(e)}")
            raise
    
    def refresh_access_token(self, refresh_token):
        """Refresh expired access token"""
        auth_client = self._get_auth_client()
        
        try:
            auth_client.refresh(refresh_token=refresh_token)
            
            return {
                'access_token': auth_client.access_token,
                'refresh_token': auth_client.refresh_token,
                'expires_in': auth_client.expires_in,
                'token_type': auth_client.token_type
            }
        except Exception as e:
            current_app.logger.error(f"Token refresh failed: {str(e)}")
            raise
    
    def revoke_token(self, refresh_token):
        """Revoke tokens when disconnecting"""
        auth_client = self._get_auth_client()
        
        try:
            auth_client.revoke(refresh_token=refresh_token)
            return True
        except Exception as e:
            current_app.logger.error(f"Token revocation failed: {str(e)}")
            return False
    
    @staticmethod
    def calculate_token_expiry(expires_in):
        """Calculate token expiration datetime"""
        return datetime.utcnow() + timedelta(seconds=expires_in)
