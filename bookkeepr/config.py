import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class Config:
    """Base configuration class."""
    
    # Flask
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    
    # Database
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///bookkeepr.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # QuickBooks / Intuit
    INTUIT_CLIENT_ID = os.environ.get('INTUIT_CLIENT_ID')
    INTUIT_CLIENT_SECRET = os.environ.get('INTUIT_CLIENT_SECRET')
    INTUIT_REDIRECT_URI = os.environ.get('INTUIT_REDIRECT_URI') or 'http://localhost:5000/auth/qbo/callback'
    INTUIT_ENVIRONMENT = os.environ.get('INTUIT_ENVIRONMENT') or 'sandbox'
    
    # QuickBooks API URLs
    QBO_BASE_URL_SANDBOX = 'https://sandbox-quickbooks.api.intuit.com'
    QBO_BASE_URL_PRODUCTION = 'https://quickbooks.api.intuit.com'
    
    @property
    def QBO_BASE_URL(self):
        return self.QBO_BASE_URL_SANDBOX if self.INTUIT_ENVIRONMENT == 'sandbox' else self.QBO_BASE_URL_PRODUCTION
    
    # OpenAI
    OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY')
    
    # Stripe
    STRIPE_PUBLISHABLE_KEY = os.environ.get('STRIPE_PUBLISHABLE_KEY')
    STRIPE_SECRET_KEY = os.environ.get('STRIPE_SECRET_KEY')
    STRIPE_WEBHOOK_SECRET = os.environ.get('STRIPE_WEBHOOK_SECRET')
    
    # Intuit QuickBooks Webhooks
    INTUIT_WEBHOOK_SECRET = os.environ.get('INTUIT_WEBHOOK_SECRET')
    INTUIT_WEBHOOK_TOKEN = os.environ.get('INTUIT_WEBHOOK_TOKEN')  # Optional: for additional verification
    
    # Subscription Prices (monthly)
    PRICE_STANDARD = 19900  # $199.00 in cents
    PRICE_SILVER = 29900    # $299.00 in cents
    PRICE_GOLD = 39900      # $399.00 in cents
    
    # Redis / Celery
    REDIS_URL = os.environ.get('REDIS_URL') or 'redis://localhost:6379/0'
    
    # Email
    EMAIL_PROVIDER = os.environ.get('EMAIL_PROVIDER') or 'smtp'
    SMTP_SERVER = os.environ.get('SMTP_SERVER')
    SMTP_PORT = int(os.environ.get('SMTP_PORT') or 587)
    SMTP_USERNAME = os.environ.get('SMTP_USERNAME')
    SMTP_PASSWORD = os.environ.get('SMTP_PASSWORD')
    
    # App Settings
    APP_NAME = os.environ.get('APP_NAME') or 'BookKeepr AI'
    APP_URL = os.environ.get('APP_URL') or 'http://localhost:5000'
    SUPPORT_EMAIL = os.environ.get('SUPPORT_EMAIL') or 'support@bookkeepr.ai'
    
    # Feature Flags
    ENABLE_QBD = os.environ.get('ENABLE_QBD', 'false').lower() == 'true'
    ENABLE_SMS_NOTIFICATIONS = os.environ.get('ENABLE_SMS_NOTIFICATIONS', 'false').lower() == 'true'
    ENABLE_EMAIL_NOTIFICATIONS = os.environ.get('ENABLE_EMAIL_NOTIFICATIONS', 'true').lower() == 'true'
    
    # Logging
    LOG_LEVEL = os.environ.get('LOG_LEVEL') or 'INFO'


class DevelopmentConfig(Config):
    """Development configuration."""
    DEBUG = True
    INTUIT_ENVIRONMENT = 'sandbox'


class ProductionConfig(Config):
    """Production configuration."""
    DEBUG = False
    INTUIT_ENVIRONMENT = 'production'
    
    # Security headers
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'


class TestingConfig(Config):
    """Testing configuration."""
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
