"""
BookKeepr AI - Flask Application Factory
"""
from flask import Flask
from .config import config_by_name
from .extensions import db, migrate, celery, login_manager, bcrypt


def create_app(config_name='development'):
    """Application factory pattern."""
    app = Flask(__name__, 
                template_folder='templates',
                static_folder='static')
    
    # Load configuration
    app.config.from_object(config_by_name[config_name])
    
    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    bcrypt.init_app(app)
    
    # Initialize Celery
    celery.conf.update(app.config)
    
    # Register blueprints
    from .routes.auth import auth_bp
    from .routes.dashboard import dashboard_bp
    from .routes.transactions import transactions_bp
    from .routes.api import api_bp
    
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(dashboard_bp, url_prefix='/dashboard')
    app.register_blueprint(transactions_bp, url_prefix='/transactions')
    app.register_blueprint(api_bp, url_prefix='/api/v1')
    
    # Root route
    @app.route('/')
    def index():
        return "BookKeepr AI - Premium Autonomous Bookkeeping"
    
    # Shell context
    @app.shell_context_processor
    def make_shell_context():
        from .models import User, Company, Transaction, Category
        return {
            'db': db,
            'User': User,
            'Company': Company,
            'Transaction': Transaction,
            'Category': Category
        }
    
    return app


def make_celery(app):
    """Create Celery instance with Flask context."""
    celery.conf.update(app.config)
    
    class ContextTask(celery.Task):
        def __call__(self, *args, **kwargs):
            with app.app_context():
                return self.run(*args, **kwargs)
    
    celery.Task = ContextTask
    return celery
