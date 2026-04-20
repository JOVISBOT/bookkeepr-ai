"""
OAuth Routes for QuickBooks Integration
Handles OAuth flow endpoints
"""
from flask import Blueprint, redirect, request, url_for, flash, session, render_template
from app.services.qb_auth import QuickBooksAuthService
from datetime import datetime, timedelta
import logging
import secrets

logger = logging.getLogger(__name__)
auth_bp = Blueprint('auth', __name__, url_prefix='/auth')


@auth_bp.route('/login')
def login():
    """
    Login page - redirects to QuickBooks OAuth
    For now, we use QB OAuth as the primary auth method
    """
    # For Phase 1, redirect to OAuth connect
    # Later we'll add email/password login
    return redirect(url_for('auth.connect'))


@auth_bp.route('/connect')
def connect():
    """
    Start OAuth flow
    Redirects user to Intuit authorization page
    """
    try:
        # Create auth service
        auth_service = QuickBooksAuthService()
        
        # Get authorization URL (AuthClient generates state automatically)
        auth_url = auth_service.get_authorization_url()
        
        # Store the state that AuthClient generated for CSRF verification
        if hasattr(auth_service.auth_client, 'state'):
            session['oauth_state'] = auth_service.auth_client.state
        
        logger.info(f"Starting OAuth flow, redirecting to Intuit...")
        return redirect(auth_url)
        
    except Exception as e:
        logger.error(f"OAuth connect failed: {e}")
        flash("Failed to start QuickBooks connection. Please try again.", "error")
        return redirect(url_for('dashboard.index'))


@auth_bp.route('/callback')
def callback():
    """
    OAuth callback endpoint
    Handles authorization code exchange
    """
    try:
        # Get authorization code and realm ID
        auth_code = request.args.get('code')
        realm_id = request.args.get('realmId')
        
        if not auth_code or not realm_id:
            logger.error("Missing auth code or realm ID")
            flash("Authorization incomplete. Please try again.", "error")
            return redirect(url_for('dashboard.index'))
        
        logger.info(f"Received callback for realm: {realm_id}")
        
        # Exchange code for tokens
        auth_service = QuickBooksAuthService()
        tokens = auth_service.exchange_code_for_token(auth_code, realm_id)
        
        # Store tokens in session
        session['qb_tokens'] = tokens
        
        # Mark user as authenticated in session (for Flask-Login)
        session['user_id'] = 'oauth_user'  # Placeholder until we implement proper user model
        session['_fresh'] = True
        
        # Create or update company record
        from app import db
        from app.models.company import Company
        
        company = Company.query.filter_by(realm_id=realm_id).first()
        if not company:
            company = Company(
                name=f"QB Company {realm_id}",
                realm_id=realm_id,
                access_token=tokens.get('access_token'),
                refresh_token=tokens.get('refresh_token'),
                token_expires_at=datetime.utcnow() + timedelta(hours=1),
                is_qbo=True
            )
            db.session.add(company)
        else:
            company.access_token = tokens.get('access_token')
            company.refresh_token = tokens.get('refresh_token')
            company.token_expires_at = datetime.utcnow() + timedelta(hours=1)
            company.last_sync = datetime.utcnow()
        
        db.session.commit()
        
        logger.info(f"Successfully connected QuickBooks for realm: {realm_id}")
        flash("QuickBooks connected successfully!", "success")
        
        return redirect(url_for('dashboard.index'))
        
    except Exception as e:
        logger.error(f"OAuth callback failed: {e}")
        flash("Failed to complete QuickBooks connection. Please try again.", "error")
        return redirect(url_for('dashboard.index'))


@auth_bp.route('/disconnect')
def disconnect():
    """
    Disconnect QuickBooks
    Revokes tokens and removes connection
    """
    try:
        tokens = session.get('qb_tokens', {})
        access_token = tokens.get('access_token')
        
        if access_token:
            auth_service = QuickBooksAuthService()
            auth_service.disconnect(access_token)
        
        # Clear tokens from session
        session.pop('qb_tokens', None)
        
        logger.info("QuickBooks disconnected")
        flash("QuickBooks disconnected successfully.", "success")
        
    except Exception as e:
        logger.error(f"Disconnect failed: {e}")
        flash("Failed to disconnect. Please try again.", "error")
    
    return redirect(url_for('dashboard.index'))


@auth_bp.route('/status')
def status():
    """
    Check connection status
    Returns JSON with connection info
    """
    tokens = session.get('qb_tokens', {})
    
    if tokens and tokens.get('access_token'):
        return {
            'connected': True,
            'realm_id': tokens.get('realm_id'),
            'has_access_token': bool(tokens.get('access_token')),
            'has_refresh_token': bool(tokens.get('refresh_token'))
        }
    
    return {
        'connected': False,
        'realm_id': None,
        'has_access_token': False,
        'has_refresh_token': False
    }
