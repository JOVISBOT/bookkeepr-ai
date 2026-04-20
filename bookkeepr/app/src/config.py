"""
Configuration settings for different environments
"""
import os
from datetime import timedelta

basedir = os.path.abspath(os.path.dirname(__file__))


class Config:
    """Base configuration."""
    # Flask
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    
    # Database
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'postgresql://postgres:postgres@localhost:5432/bookkeepr'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_size': 10,
        'pool_recycle': 3600,
        'pool_pre_ping': True,
    }
    
    # Redis / Celery
    REDIS_URL = os.environ.get('REDIS_URL') or 'redis://localhost:6379/0'
    CELERY_BROKER_URL = os.environ.get('CELERY_BROKER_URL') or REDIS_URL
    CELERY_RESULT_BACKEND = os.environ.get('CELERY_RESULT_BACKEND') or REDIS_URL
    
    # QuickBooks OAuth
    QBO_CLIENT_ID = os.environ.get('QBO_CLIENT_ID')
    QBO_CLIENT_SECRET = os.environ.get('QBO_CLIENT_SECRET')
    QBO_SANDBOX_MODE = os.environ.get('QBO_SANDBOX_MODE', 'true').lower() == 'true'
    
    # QBO Base URLs
    QBO_SANDBOX_BASE_URL = 'https://sandbox-quickbooks.api.intuit.com'
    QBO_PRODUCTION_BASE_URL = 'https://quickbooks.api.intuit.com'
    QBO_BASE_URL = QBO_SANDBOX_BASE_URL if QBO_SANDBOX_MODE else QBO_PRODUCTION_BASE_URL
    
    # Intuit OAuth URLs
    INTUIT_AUTH_URL = 'https://appcenter.intuit.com/connect/oauth2'
    INTUIT_TOKEN_URL = 'https://oauth.platform.intuit.com/oauth2/v1/tokens/bearer'
    INTUIT_REFRESH_URL = 'https://oauth.platform.intuit.com/oauth2/v1/tokens/bearer'
    
    # Encryption
    ENCRYPTION_KEY = os.environ.get('ENCRYPTION_KEY')
    
    # Session
    PERMANENT_SESSION_LIFETIME = timedelta(days=7)
    
    # Mail (for notifications)
    MAIL_SERVER = os.environ.get('MAIL_SERVER') or 'smtp.gmail.com'
    MAIL_PORT = int(os.environ.get('MAIL_PORT') or 587)
    MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS', 'true').lower() == 'true'
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    
    # Application settings
    TRANSACTIONS_PER_PAGE = 50
    AUTO_CATEGORIZE_THRESHOLD = 0.8  # 80% confidence


class DevelopmentConfig(Config):
    """Development configuration."""
    DEBUG = True
    QBO_SANDBOX_MODE = True
    

class TestingConfig(Config):
    """Testing configuration."""
    TESTING = True
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = os.environ.get('TEST_DATABASE_URL') or \
        'postgresql://postgres:postgres@localhost:5432/bookkeepr_test'
    WTF_CSRF_ENABLED = False
    QBO_SANDBOX_MODE = True


class StagingConfig(Config):
    """Staging configuration."""
    DEBUG = False
    QBO_SANDBOX_MODE = True


class ProductionConfig(Config):
    """Production configuration."""
    DEBUG = False
    QBO_SANDBOX_MODE = False
    
    # Production database pooling
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_size': 20,
        'max_overflow': 10,
        'pool_recycle': 3600,
        'pool_pre_ping': True,
    }


# Config dictionary
config_by_name = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'staging': StagingConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}
