"""BookKeepr AI - Flask Extensions"""
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from flask_wtf.csrf import CSRFProtect
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from sqlalchemy import event
from sqlalchemy.engine import Engine
import os


# Database
db = SQLAlchemy()
migrate = Migrate()

# Authentication
login_manager = LoginManager()
login_manager.login_view = 'auth.login'
login_manager.login_message = 'Please log in to access this page.'
login_manager.login_message_category = 'info'

# CSRF
csrf = CSRFProtect()

# Rate limiter — swap storage_uri to Redis in prod: redis://localhost:6379
# Default: 300 req/hour globally; sensitive endpoints add per-route limits
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=['300 per hour', '30 per minute'],
    storage_uri=__import__('os').environ.get('REDIS_URL', 'memory://'),
)


def _set_sqlite_wal_mode(dbapi_conn, connection_record):
    """Enable WAL mode for SQLite on connection"""
    cursor = dbapi_conn.cursor()
    cursor.execute("PRAGMA journal_mode=WAL")
    cursor.execute("PRAGMA synchronous=NORMAL")
    cursor.execute("PRAGMA cache_size=10000")
    cursor.close()


def init_extensions(app):
    """Initialize all Flask extensions"""
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    csrf.init_app(app)
    limiter.init_app(app)

    # Exempt JSON API endpoints from CSRF (they use token auth instead)
    from flask import request as _req

    @app.after_request
    def _security_headers(response):
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['X-Frame-Options'] = 'SAMEORIGIN'
        response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        return response

    # Enable SQLite WAL mode for better concurrency
    if 'sqlite' in app.config.get('SQLALCHEMY_DATABASE_URI', '').lower():
        with app.app_context():
            @event.listens_for(Engine, "connect")
            def enable_wal(dbapi_conn, connection_record):
                _set_sqlite_wal_mode(dbapi_conn, connection_record)
        app.logger.info("SQLite WAL mode enabled for improved concurrency")
