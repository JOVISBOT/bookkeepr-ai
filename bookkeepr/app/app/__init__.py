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
    from app.routes.billing import bp as billing_bp
    from app.routes.charts import bp as charts_bp
    from app.routes.reports import bp as reports_bp
    from app.routes.ai import bp as ai_bp
    from app.routes.pricing import bp as pricing_bp
    from app.routes.review import bp as review_bp
    from app.routes.admin import bp as admin_bp
    from app.routes.ai_enhanced import bp as ai_enhanced_bp
    from app.routes.banks import bp as banks_bp
    from app.routes.clients import bp as clients_bp
    from app.routes.mfa import bp as mfa_bp
    from app.routes.imports import bp as imports_bp
    from app.routes.portal import bp as portal_bp
    from app.routes.copilot import bp as copilot_bp

    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(dashboard_bp, url_prefix='/dashboard')
    app.register_blueprint(api_bp, url_prefix='/api/v1')
    app.register_blueprint(quickbooks_bp, url_prefix='/quickbooks')
    app.register_blueprint(reconciliation_bp, url_prefix='/api/v1')
    app.register_blueprint(billing_bp)
    app.register_blueprint(charts_bp)
    app.register_blueprint(reports_bp)
    # Reports blueprint handles both /dashboard/reports and /api/v1/reports/*
    app.register_blueprint(ai_bp, url_prefix='/api/v1/ai')
    app.register_blueprint(pricing_bp)
    app.register_blueprint(review_bp, url_prefix='/dashboard')
    app.register_blueprint(admin_bp)
    app.register_blueprint(ai_enhanced_bp, url_prefix='/api/v1/ai')
    app.register_blueprint(banks_bp)
    app.register_blueprint(clients_bp, url_prefix='/dashboard/clients')
    app.register_blueprint(mfa_bp, url_prefix='/auth')
    app.register_blueprint(imports_bp, url_prefix='/dashboard/imports')
    app.register_blueprint(portal_bp)
    app.register_blueprint(copilot_bp)

    # Exempt JSON/API blueprints from CSRF (they use session/token auth, not form tokens)
    from extensions import csrf
    for _bp in (api_bp, reconciliation_bp, ai_bp, ai_enhanced_bp, quickbooks_bp, copilot_bp):
        csrf.exempt(_bp)
    
    # Register catch-all route for React frontend (after all API routes)
    from flask import send_from_directory
    import os
    
    @app.route('/assets/<path:filename>')
    def serve_assets(filename):
        """Serve React static assets"""
        static_dir = os.path.join(os.path.dirname(__file__), '..', 'static', 'assets')
        return send_from_directory(static_dir, filename)
    
    @app.route('/static/css/<path:filename>')
    def serve_css(filename):
        """Serve theme CSS"""
        css_dir = os.path.join(os.path.dirname(__file__), '..', 'static', 'css')
        return send_from_directory(css_dir, filename)
    
    @app.route('/app', defaults={'path': ''})
    @app.route('/app/<path:path>')
    def serve_react(path):
        """Serve React app for /app routes"""
        static_dir = os.path.join(os.path.dirname(__file__), '..', 'static')
        
        # Check if file exists in dist folder
        file_path = os.path.join(static_dir, path)
        if path and os.path.exists(file_path) and os.path.isfile(file_path):
            return send_from_directory(static_dir, path)
            
        # Otherwise serve index.html for client-side routing
        return send_from_directory(static_dir, 'index.html')
    
    # Ensure all tables exist (safe — only creates missing tables)
    with app.app_context():
        db.create_all()

    # Warn if QBO sandbox credentials are used in production
    import os as _os
    if _os.environ.get('FLASK_ENV') == 'production' and _os.environ.get('INTUIT_ENVIRONMENT', 'sandbox') == 'sandbox':
        import logging as _logging
        _logging.getLogger(__name__).warning(
            'WARNING: INTUIT_ENVIRONMENT=sandbox while FLASK_ENV=production. '
            'Switch to production QBO credentials before going live.'
        )

    # Start background QBO auto-sync (every 30 min) — skipped in testing
    if config_name != 'testing':
        try:
            from app.routes.quickbooks.scheduler import init_scheduler
            init_scheduler(app)
        except Exception:
            pass  # APScheduler not installed or disabled — manual sync still works

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
    from flask import render_template, request, jsonify
    
    @app.errorhandler(400)
    def bad_request_error(error):
        if request.is_json:
            return jsonify({'success': False, 'error': 'Bad request'}), 400
        return render_template('errors/400.html'), 400
    
    @app.errorhandler(401)
    def unauthorized_error(error):
        if request.is_json:
            return jsonify({'success': False, 'error': 'Authentication required'}), 401
        return render_template('errors/401.html'), 401
    
    @app.errorhandler(403)
    def forbidden_error(error):
        if request.is_json:
            return jsonify({'success': False, 'error': 'Access denied'}), 403
        return render_template('errors/403.html'), 403
    
    @app.errorhandler(404)
    def not_found_error(error):
        if request.is_json:
            return jsonify({'success': False, 'error': 'Resource not found'}), 404
        return render_template('errors/404.html'), 404
    
    @app.errorhandler(422)
    def unprocessable_error(error):
        if request.is_json:
            return jsonify({'success': False, 'error': 'Validation failed'}), 422
        return render_template('errors/422.html'), 422
    
    @app.errorhandler(500)
    def internal_error(error):
        db.session.rollback()
        app.logger.error(f'Internal error: {error}', exc_info=True)
        if request.is_json:
            return jsonify({'success': False, 'error': 'Internal server error'}), 500
        return render_template('errors/500.html'), 500
    
    @app.errorhandler(Exception)
    def catch_all_error(error):
        from werkzeug.exceptions import HTTPException
        if isinstance(error, HTTPException):
            return error
        db.session.rollback()
        app.logger.error(f'Unhandled exception: {error}', exc_info=True)
        if request.is_json:
            return jsonify({'success': False, 'error': 'Unexpected error occurred'}), 500
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
