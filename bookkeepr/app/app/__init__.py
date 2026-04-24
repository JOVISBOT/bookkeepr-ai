"""BookKeepr AI - Flask Application Factory"""
from flask import Flask
from config import config
from extensions import init_extensions, db, login_manager


def create_app(config_name='default'):
    """Application factory pattern"""
    app = Flask(__name__)
    
    # Load configuration
    app.config.from_object(config[config_name])
    
    # Initialize extensions
    init_extensions(app)
    
    # Register blueprints FIRST (before catch-all route)
    from app.routes.main import bp as main_bp
    from app.routes.auth import bp as auth_bp
    from app.routes.dashboard import bp as dashboard_bp
    from app.routes.api import bp as api_bp
    from app.routes.quickbooks import bp as quickbooks_bp
    from app.routes.reconciliation import bp as reconciliation_bp
    from app.routes.billing import billing_bp
    from app.routes.charts import bp as charts_bp
    from app.routes.reports import bp as reports_bp
    from app.routes.ai import bp as ai_bp
    
    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(dashboard_bp, url_prefix='/dashboard')
    app.register_blueprint(api_bp, url_prefix='/api/v1')  # Added prefix
    app.register_blueprint(quickbooks_bp, url_prefix='/quickbooks')
    app.register_blueprint(reconciliation_bp, url_prefix='/api/v1')
    app.register_blueprint(billing_bp)
    app.register_blueprint(charts_bp)
    app.register_blueprint(reports_bp)
    app.register_blueprint(ai_bp, url_prefix='/api/v1/ai')
    
    # Register catch-all route LAST (after all blueprints)
    from flask import send_from_directory
    import os
    
    @app.route('/app', defaults={'path': ''})
    @app.route('/app/<path:path>')
    def serve_react(path):
        """Serve React app for /app routes only"""
        static_dir = os.path.join(os.path.dirname(__file__), '..', 'static')
        
        # Check if file exists in dist folder
        file_path = os.path.join(static_dir, path)
        if path and os.path.exists(file_path) and os.path.isfile(file_path):
            return send_from_directory(static_dir, path)
            
        # Otherwise serve index.html for client-side routing
        return send_from_directory(static_dir, 'index.html')
    
    # Register error handlers
    register_error_handlers(app)
    
    # Register template filters
    register_template_filters(app)
    
    # Register user loader for Flask-Login
    from app.models.user import User
    
    @login_manager.user_loader
    def load_user(user_id):
        """Load user by ID for Flask-Login"""
        return User.query.get(int(user_id))
    
    return app


def register_error_handlers(app):
    """Register error handlers"""
    from flask import render_template
    
    @app.errorhandler(404)
    def not_found_error(error):
        return render_template('errors/404.html'), 404
    
    @app.errorhandler(500)
    def internal_error(error):
        from extensions import db
        db.session.rollback()
        return render_template('errors/500.html'), 500


def register_template_filters(app):
    """Register custom template filters"""
    
    @app.template_filter('currency')
    def currency_filter(value):
        """Format number as currency"""
        if value is None:
            return '$0.00'
        return f'${value:,.2f}'
    
    @app.template_filter('date_format')
    def date_format_filter(value, format='%Y-%m-%d'):
        """Format date"""
        if value is None:
            return ''
        return value.strftime(format)
