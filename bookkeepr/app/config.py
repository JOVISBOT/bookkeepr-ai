"""BookKeepr AI - Configuration"""
import os
from datetime import timedelta


class Config:
    """Base configuration"""
    
    # Flask
    @property
    def SECRET_KEY(self):
        """Get SECRET_KEY from environment"""
        key = os.environ.get('SECRET_KEY')
        if not key or len(key) < 16:
            return 'your-super-secret-key-2026-bookkeepr-ai'
        return key
    
    # Database
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        'DATABASE_URL', 
        'sqlite:///bookkeepr.db'  # Default to SQLite for Render
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Session
    PERMANENT_SESSION_LIFETIME = timedelta(days=7)
    
    # QuickBooks
    INTUIT_CLIENT_ID = os.environ.get('INTUIT_CLIENT_ID')
    INTUIT_CLIENT_SECRET = os.environ.get('INTUIT_CLIENT_SECRET')
    INTUIT_SANDBOX_MODE = os.environ.get('INTUIT_SANDBOX_MODE', 'true').lower() == 'true'
    INTUIT_REDIRECT_URI = os.environ.get('INTUIT_REDIRECT_URI', 'http://localhost:5000/auth/callback')
    INTUIT_SCOPES = os.environ.get('INTUIT_SCOPES', 'openid profile email com.intuit.quickbooks.accounting')
    
    @property
    def INTUIT_BASE_URL(self):
        """Base URL for Intuit API"""
        return 'https://sandbox-quickbooks.api.intuit.com' if self.INTUIT_SANDBOX_MODE else 'https://quickbooks.api.intuit.com'
    
    @property
    def INTUIT_AUTH_BASE_URL(self):
        """Base URL for Intuit OAuth"""
        return 'https://sandbox-accounts.platform.intuit.com' if self.INTUIT_SANDBOX_MODE else 'https://accounts.platform.intuit.com'
    
    # Application
    APP_NAME = os.environ.get('APP_NAME', 'BookKeepr AI')
    APP_URL = os.environ.get('APP_URL', 'http://localhost:5000')
    
    # Redis/Celery
    REDIS_URL = os.environ.get('REDIS_URL', 'redis://localhost:6379/0')
    
    # Logging
    LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO')


class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True
    SQLALCHEMY_ECHO = True


class ProductionConfig(Config):
    """Production configuration"""
    DEBUG = False
    SQLALCHEMY_ECHO = False


class TestingConfig(Config):
    """Testing configuration"""
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    WTF_CSRF_ENABLED = False


# Configuration dictionary
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}
