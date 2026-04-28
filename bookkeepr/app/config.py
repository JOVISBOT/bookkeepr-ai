"""BookKeepr AI - Configuration"""
import os
from datetime import timedelta


def _require_env(name: str, fallback=None):
    """Return env var value; raise in production if missing and no fallback."""
    value = os.environ.get(name)
    if not value:
        if os.environ.get('FLASK_ENV') == 'production':
            raise EnvironmentError(f"Required environment variable {name!r} is not set.")
        return fallback() if callable(fallback) else fallback
    return value


class Config:
    """Base configuration"""

    # Flask
    SECRET_KEY = _require_env('SECRET_KEY', fallback=lambda: os.urandom(32).hex())
    
    # Database - resolve to absolute path for instance/bookkeepr.db
    _BASE_DIR = os.path.abspath(os.path.dirname(__file__))
    _DB_PATH = os.path.join(_BASE_DIR, 'instance', 'bookkeepr.db').replace('\\', '/')
    _DEFAULT_DB = f'sqlite:///{_DB_PATH}'
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        'DATABASE_URL', 
        _DEFAULT_DB
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # SQLite WAL Mode for better concurrency
    SQLALCHEMY_ENGINE_OPTIONS = {
        'connect_args': {
            'check_same_thread': False,
        },
        'pool_pre_ping': True,
        'pool_recycle': 300,
    }
    
    # Enable WAL mode on connection
    @staticmethod
    def init_app(app):
        """Initialize application with WAL mode"""
        with app.app_context():
            from sqlalchemy import event
            from sqlalchemy.engine import Engine
            
            @event.listens_for(Engine, "connect")
            def set_sqlite_pragma(dbapi_conn, connection_record):
                cursor = dbapi_conn.cursor()
                cursor.execute("PRAGMA journal_mode=WAL")
                cursor.execute("PRAGMA synchronous=NORMAL")
                cursor.execute("PRAGMA cache_size=10000")
                cursor.close()
    
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
    
    # Token encryption (Fernet) — generate with: python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
    FERNET_KEY = _require_env('FERNET_KEY')

    # Application
    APP_NAME = os.environ.get('APP_NAME', 'BookKeepr AI')
    APP_URL = os.environ.get('APP_URL', 'http://localhost:5000')

    # Email (SendGrid)
    SENDGRID_API_KEY = os.environ.get('SENDGRID_API_KEY')  # optional — falls back to console log
    MAIL_FROM = os.environ.get('MAIL_FROM', 'noreply@bookkeepr.ai')

    # Stripe (optional — falls back to demo mode)
    STRIPE_SECRET_KEY = os.environ.get('STRIPE_SECRET_KEY')
    STRIPE_PUBLISHABLE_KEY = os.environ.get('STRIPE_PUBLISHABLE_KEY')
    STRIPE_WEBHOOK_SECRET = os.environ.get('STRIPE_WEBHOOK_SECRET')

    # QuickBooks environment
    INTUIT_ENVIRONMENT = os.environ.get('INTUIT_ENVIRONMENT', 'sandbox')

    # Redis / rate limiter
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

    # Force https:// in url_for() — critical for password reset links in email
    PREFERRED_URL_SCHEME = 'https'

    # Secure cookies — requires HTTPS
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    REMEMBER_COOKIE_SECURE = True
    REMEMBER_COOKIE_HTTPONLY = True

    # PostgreSQL-compatible engine options (drop SQLite-only check_same_thread)
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_pre_ping': True,
        'pool_recycle': 300,
        'pool_size': 5,
        'max_overflow': 10,
    }


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
