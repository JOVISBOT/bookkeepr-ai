"""BookKeepr AI - Flask Extensions"""
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
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
    
    # Enable SQLite WAL mode for better concurrency
    if 'sqlite' in app.config.get('SQLALCHEMY_DATABASE_URI', '').lower():
        with app.app_context():
            @event.listens_for(Engine, "connect")
            def enable_wal(dbapi_conn, connection_record):
                _set_sqlite_wal_mode(dbapi_conn, connection_record)
        app.logger.info("SQLite WAL mode enabled for improved concurrency")
