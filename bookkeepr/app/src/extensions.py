"""
Flask extensions initialization
Extensions are created here and initialized in create_app()
"""
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from flask_bcrypt import Bcrypt
from celery import Celery

# Database
db = SQLAlchemy()

# Migrations
migrate = Migrate()

# Authentication
login_manager = LoginManager()
login_manager.login_view = 'auth.login'
login_manager.login_message = 'Please log in to access this page.'
login_manager.login_message_category = 'info'

# Password hashing
bcrypt = Bcrypt()

# Celery - will be configured in create_app
celery = Celery('bookkeepr')
