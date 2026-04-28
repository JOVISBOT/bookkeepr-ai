"""
QuickBooks OAuth Service
Handles OAuth 2.0 flow for QuickBooks Online
"""
from intuitlib.client import AuthClient
from intuitlib.enums import Scopes
from intuitlib.exceptions import AuthClientError
import os
from typing import Optional, Dict, Callable
from functools import wraps
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


class QuickBooksAuthService:
    """Service for handling QuickBooks OAuth authentication"""
    
    def __init__(self):
        self.client_id = os.getenv('INTUIT_CLIENT_ID')
        self.client_secret = os.getenv('INTUIT_CLIENT_SECRET')
        self.redirect_uri = os.getenv('INTUIT_REDIRECT_URI', 'http://localhost:5000/auth/callback')
        self.environment = os.getenv('INTUIT_ENVIRONMENT', 'sandbox')
        
        if not all([self.client_id, self.client_secret]):
            raise ValueError("INTUIT_CLIENT_ID and INTUIT_CLIENT_SECRET must be set")
        
        self.auth_client = AuthClient(
            client_id=self.client_id,
            client_secret=self.client_secret,
            environment=self.environment,
            redirect_uri=self.redirect_uri
        )
    
    def get_authorization_url(self, state: Optional[str] = None) -> str:
        """
        Generate OAuth authorization URL
        
        Args:
            state: Optional state parameter for CSRF protection
            
        Returns:
            Authorization URL to redirect user to
        """
        scopes = [
            Scopes.ACCOUNTING,  # Read/write accounting data
            Scopes.OPENID,     # OpenID Connect
            Scopes.PROFILE,    # User profile info
            Scopes.EMAIL       # User email
        ]
        
        kwargs = {}
        if state:
            kwargs['state'] = state
        auth_url = self.auth_client.get_authorization_url(scopes, **kwargs)
        logger.info(f"Generated auth URL (state={'set' if state else 'auto'}): {auth_url[:80]}...")
        return auth_url
    
    def exchange_code_for_token(self, auth_code: str, realm_id: str) -> Dict:
        """
        Exchange authorization code for access token
        
        Args:
            auth_code: Authorization code from callback
            realm_id: QuickBooks company realm ID
            
        Returns:
            Dictionary with tokens and metadata
        """
        try:
            self.auth_client.get_bearer_token(auth_code, realm_id=realm_id)
            
            tokens = {
                'access_token': self.auth_client.access_token,
                'refresh_token': self.auth_client.refresh_token,
                'realm_id': realm_id,
                'expires_in': self.auth_client.expires_in,
                'token_type': 'Bearer'
            }
            
            logger.info(f"Successfully obtained tokens for realm: {realm_id}")
            return tokens
            
        except Exception as e:
            logger.error(f"Token exchange failed: {e}")
            raise
    
    def refresh_access_token(self, refresh_token: str) -> Dict:
        """
        Refresh expired access token
        
        Args:
            refresh_token: Valid refresh token
            
        Returns:
            Dictionary with new tokens
        """
        try:
            self.auth_client.refresh(refresh_token=refresh_token)
            
            tokens = {
                'access_token': self.auth_client.access_token,
                'refresh_token': self.auth_client.refresh_token,
                'expires_in': self.auth_client.expires_in,
                'token_type': 'Bearer'
            }
            
            logger.info("Successfully refreshed access token")
            return tokens
            
        except Exception as e:
            logger.error(f"Token refresh failed: {e}")
            raise
    
    def disconnect(self, access_token: str) -> bool:
        """
        Disconnect/revoke QuickBooks connection
        
        Args:
            access_token: Current access token
            
        Returns:
            True if successful
        """
        try:
            self.auth_client.revoke(access_token=access_token)
            logger.info("Successfully revoked QuickBooks connection")
            return True
        except Exception as e:
            logger.error(f"Disconnect failed: {e}")
            return False
    
    def is_token_valid(self, access_token: str) -> bool:
        """
        Check if access token is still valid
        
        Args:
            access_token: Token to validate
            
        Returns:
            True if valid
        """
        # Tokens expire after 1 hour
        # This is a simple check - in production, track expiration time
        return bool(access_token and len(access_token) > 10)


from contextlib import contextmanager
from typing import Any
import threading

# Thread-local storage for auth service instances
_local = threading.local()


def get_auth_service() -> QuickBooksAuthService:
    """Get or create thread-local auth service instance"""
    if not hasattr(_local, 'auth_service'):
        _local.auth_service = QuickBooksAuthService()
    return _local.auth_service


class TokenRefreshError(Exception):
    """Raised when token refresh fails"""
    pass


def refresh_company_token(company) -> Dict:
    """
    Refresh a company's access token.
    
    Args:
        company: Company model with refresh_token
        
    Returns:
        Dict with new tokens
        
    Raises:
        TokenRefreshError: If refresh fails
    """
    if not company.refresh_token:
        logger.error(f"No refresh token available for company {company.id}")
        raise TokenRefreshError("No refresh token available")
    
    try:
        auth_service = get_auth_service()
        tokens = auth_service.refresh_access_token(company.refresh_token)
        
        # Update company tokens
        company.access_token = tokens['access_token']
        company.refresh_token = tokens['refresh_token']
        company.token_expires_at = datetime.utcnow() + timedelta(seconds=tokens['expires_in'])
        
        logger.info(f"Token refreshed successfully for company {company.id}, "
                   f"expires at {company.token_expires_at}")
        
        return tokens
        
    except AuthClientError as e:
        logger.error(f"Token refresh failed for company {company.id}: {e}")
        # Mark connection as failed
        company.is_connected = False
        raise TokenRefreshError(f"Token refresh failed: {e}")


@contextmanager
def ensure_valid_token_context(company):
    """
    Context manager that ensures a valid token before yielding.
    
    Automatically refreshes the token if needed and commits to database.
    
    Args:
        company: Company model with token fields
        
    Usage:
        with ensure_valid_token_context(company):
            # Make API calls here
            sync_data(company)
    """
    from app import db
    
    if company and hasattr(company, 'needs_token_refresh'):
        if company.needs_token_refresh():
            logger.info(f"Token needs refresh for company {company.id}")
            refresh_company_token(company)
            db.session.commit()
    
    try:
        yield company
    except AuthClientError as e:
        # If auth error during execution, try refresh once more
        if 'authentication' in str(e).lower() or 'unauthorized' in str(e).lower():
            logger.warning(f"Auth error during operation, attempting refresh: {e}")
            refresh_company_token(company)
            db.session.commit()
            # Re-raise to let caller retry
            raise
        raise


def ensure_valid_token(func: Callable) -> Callable:
    """
    Decorator that ensures a valid QuickBooks token before API calls.
    
    Automatically refreshes the token if:
    - Token is expired (or < 5 minutes until expiry)
    - The company object has needs_token_refresh() method that returns True
    
    The decorated function must accept 'company' as first argument or kwarg.
    Refreshes are committed to database before the function executes.
    
    If the function raises an AuthClientError, attempts one automatic retry
    after refreshing the token.
    
    Usage:
        @ensure_valid_token
        def sync_accounts(self, company, ...):
            ...
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        from app import db
        
        # Find company object in args or kwargs
        company = None
        
        for idx, arg in enumerate(args):
            if hasattr(arg, 'needs_token_refresh'):
                company = arg
                break
        
        if not company and 'company' in kwargs:
            company = kwargs['company']
        
        if company and hasattr(company, 'needs_token_refresh'):
            if company.needs_token_refresh():
                logger.info(f"Token needs refresh for company {company.id} (via decorator)")
                try:
                    refresh_company_token(company)
                    db.session.commit()
                    logger.info(f"Token refreshed and committed for company {company.id}")
                except TokenRefreshError:
                    db.session.commit()  # Commit the is_connected=False change
                    raise
        
        try:
            return func(*args, **kwargs)
        except AuthClientError as e:
            error_msg = str(e).lower()
            # Check if it's an auth error that might benefit from refresh
            if any(term in error_msg for term in ['token', 'expired', 'unauthorized', 'authentication']):
                logger.warning(f"Auth error during {func.__name__}, attempting retry with refresh: {e}")
                
                if company and company.refresh_token:
                    try:
                        refresh_company_token(company)
                        db.session.commit()
                        logger.info(f"Retrying {func.__name__} after successful refresh")
                        return func(*args, **kwargs)  # Retry once
                    except TokenRefreshError:
                        db.session.commit()
                        company.is_connected = False
            raise
    
    return wrapper


def with_auto_refresh(company_attr: str = 'company'):
    """
    Decorator factory for methods that need token refresh.
    
    Allows specifying which attribute contains the company object.
    
    Usage:
        @with_auto_refresh('company')
        def fetch_data(self, ...):
            # self.company will be checked/refreshed
            ...
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(instance, *args, **kwargs):
            from app import db
            
            company = getattr(instance, company_attr, None)
            
            if company and hasattr(company, 'needs_token_refresh'):
                if company.needs_token_refresh():
                    logger.info(f"Token needs refresh for company {company.id} (via with_auto_refresh)")
                    try:
                        refresh_company_token(company)
                        db.session.commit()
                    except TokenRefreshError:
                        db.session.commit()
                        raise
            
            try:
                return func(instance, *args, **kwargs)
            except AuthClientError as e:
                error_msg = str(e).lower()
                if any(term in error_msg for term in ['token', 'expired', 'unauthorized', 'authentication']):
                    if company and company.refresh_token:
                        try:
                            refresh_company_token(company)
                            db.session.commit()
                            return func(instance, *args, **kwargs)  # Retry
                        except TokenRefreshError:
                            db.session.commit()
                            company.is_connected = False
                raise
        
        return wrapper
    return decorator
