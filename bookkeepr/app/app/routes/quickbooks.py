"""QuickBooks Routes - OAuth and Connection Management"""
from flask import Blueprint, render_template, redirect, url_for, flash, request, session, current_app
from flask_login import login_required, current_user
from extensions import db
from app.models.company import Company
from app.services.auth_service import AuthService

bp = Blueprint('quickbooks', __name__)


@bp.route('/connect')
@login_required
def connect():
    """Initiate QuickBooks OAuth connection"""
    try:
        auth_service = AuthService()
        auth_url = auth_service.get_authorization_url()
        
        # Store state in session for CSRF protection
        return redirect(auth_url)
        
    except Exception as e:
        current_app.logger.error(f"OAuth initiation failed: {str(e)}")
        flash('Failed to initiate QuickBooks connection. Please try again.', 'error')
        return redirect(url_for('dashboard.company_settings'))


@bp.route('/callback')
def callback():
    """Handle OAuth callback from Intuit"""
    auth_code = request.args.get('code')
    realm_id = request.args.get('realmId')
    state = request.args.get('state')
    
    if not auth_code or not realm_id:
        flash('Authentication failed. Please try again.', 'error')
        return redirect(url_for('dashboard.company_settings'))
    
    try:
        # Exchange code for tokens
        auth_service = AuthService()
        tokens = auth_service.exchange_code_for_tokens(auth_code, realm_id)
        
        # Calculate token expiry
        from app.services.auth_service import AuthService
        expires_at = AuthService.calculate_token_expiry(tokens['expires_in'])
        
        # Create or update company connection
        company = Company.query.filter_by(qbo_realm_id=realm_id).first()
        
        if not company:
            company = Company(
                user_id=current_user.id,
                qbo_realm_id=realm_id
            )
            db.session.add(company)
        
        # Update tokens
        company.access_token = tokens['access_token']
        company.refresh_token = tokens['refresh_token']
        company.token_expires_at = expires_at
        company.is_connected = True
        
        db.session.commit()
        
        # Sync company info
        from app.services.sync_service import SyncService
        sync_service = SyncService(company)
        sync_service.sync_company_info()
        
        flash('Successfully connected to QuickBooks!', 'success')
        return redirect(url_for('dashboard.index'))
        
    except Exception as e:
        current_app.logger.error(f"OAuth callback failed: {str(e)}")
        flash('Failed to complete QuickBooks connection. Please try again.', 'error')
        return redirect(url_for('dashboard.company_settings'))


@bp.route('/disconnect/<int:company_id>')
@login_required
def disconnect(company_id):
    """Disconnect QuickBooks company"""
    company = Company.query.filter_by(id=company_id, user_id=current_user.id).first_or_404()
    
    try:
        # Revoke tokens
        if company.refresh_token:
            auth_service = AuthService()
            auth_service.revoke_token(company.refresh_token)
        
        # Update company
        company.is_connected = False
        company.access_token = None
        company.refresh_token = None
        company.token_expires_at = None
        company.disconnected_at = db.func.now()
        
        db.session.commit()
        
        flash('QuickBooks connection has been disconnected.', 'info')
        
    except Exception as e:
        current_app.logger.error(f"Disconnect failed: {str(e)}")
        flash('Error disconnecting from QuickBooks.', 'error')
    
    return redirect(url_for('dashboard.company_settings'))


@bp.route('/sync/<int:company_id>')
@login_required
def sync(company_id):
    """Trigger manual sync for a company"""
    company = Company.query.filter_by(id=company_id, user_id=current_user.id).first_or_404()
    
    if not company.is_connected:
        flash('Company is not connected to QuickBooks.', 'error')
        return redirect(url_for('dashboard.company_settings'))
    
    try:
        from app.services.sync_service import SyncService
        
        sync_service = SyncService(company)
        result = sync_service.run_full_sync()
        
        flash('Sync completed successfully!', 'success')
        
    except Exception as e:
        current_app.logger.error(f"Sync failed: {str(e)}")
        flash('Sync failed. Please try again.', 'error')
    
    return redirect(url_for('dashboard.index'))


@bp.route('/status/<int:company_id>')
@login_required
def status(company_id):
    """Check connection status"""
    company = Company.query.filter_by(id=company_id, user_id=current_user.id).first_or_404()
    
    return {
        'is_connected': company.is_connected,
        'last_sync_at': company.last_sync_at.isoformat() if company.last_sync_at else None,
        'sync_status': company.sync_status,
        'company_name': company.qbo_company_name
    }
