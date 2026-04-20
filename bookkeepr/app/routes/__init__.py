"""
Routes Package
"""
from app.routes.auth import bp as auth_bp
from app.routes.dashboard import bp as dashboard_bp
from app.routes.api import api_bp as api_bp

__all__ = ['auth_bp', 'dashboard_bp', 'api_bp']