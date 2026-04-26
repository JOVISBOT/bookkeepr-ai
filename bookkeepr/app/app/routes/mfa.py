"""MFA setup/verify routes"""
from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from flask_login import login_required, current_user, login_user
from extensions import db
from app.models import User, AuditLog
from app.services.mfa_service import generate_secret, generate_qr_code, verify_token

bp = Blueprint('mfa', __name__, url_prefix='/mfa')


@bp.route('/setup', methods=['GET', 'POST'])
@login_required
def setup():
    """Setup MFA - show QR code for Google Authenticator"""
    if current_user.mfa_enabled:
        flash('MFA is already enabled. Disable first to re-setup.', 'info')
        return redirect(url_for('dashboard.index'))
    
    # Generate or use existing draft secret in session
    if 'mfa_draft_secret' not in session:
        session['mfa_draft_secret'] = generate_secret()
    
    secret = session['mfa_draft_secret']
    qr_code = generate_qr_code(secret, current_user.email)
    
    if request.method == 'POST':
        token = request.form.get('token', '').strip()
        if verify_token(secret, token):
            # Save secret to user
            current_user.mfa_secret = secret
            current_user.mfa_enabled = True
            
            AuditLog.log(
                action='mfa_enabled',
                target_table='users',
                target_id=current_user.id,
                user=current_user,
                tenant_id=current_user.tenant_id,
                request=request,
            )
            db.session.commit()
            
            session.pop('mfa_draft_secret', None)
            flash('MFA enabled successfully! Save your backup codes.', 'success')
            return redirect(url_for('dashboard.index'))
        else:
            flash('Invalid token. Please try again.', 'error')
    
    return render_template('mfa/setup.html', secret=secret, qr_code=qr_code)


@bp.route('/disable', methods=['POST'])
@login_required
def disable():
    """Disable MFA (require current password to confirm)"""
    password = request.form.get('password', '')
    if not current_user.check_password(password):
        flash('Invalid password', 'error')
        return redirect(url_for('dashboard.index'))
    
    current_user.mfa_enabled = False
    current_user.mfa_secret = None
    
    AuditLog.log(
        action='mfa_disabled',
        target_table='users',
        target_id=current_user.id,
        user=current_user,
        tenant_id=current_user.tenant_id,
        request=request,
    )
    db.session.commit()
    
    flash('MFA disabled.', 'info')
    return redirect(url_for('dashboard.index'))


@bp.route('/verify', methods=['GET', 'POST'])
def verify():
    """Verify MFA token during login flow"""
    user_id = session.get('mfa_pending_user_id')
    if not user_id:
        return redirect(url_for('auth.login'))
    
    user = User.query.get(user_id)
    if not user:
        session.pop('mfa_pending_user_id', None)
        return redirect(url_for('auth.login'))
    
    if request.method == 'POST':
        token = request.form.get('token', '').strip()
        if verify_token(user.mfa_secret, token):
            # Complete login
            login_user(user, remember=session.get('mfa_pending_remember', False))
            session.pop('mfa_pending_user_id', None)
            session.pop('mfa_pending_remember', None)
            
            from datetime import datetime
            user.last_login_at = datetime.utcnow()
            
            AuditLog.log(
                action='login_mfa',
                target_table='users',
                target_id=user.id,
                user=user,
                request=request,
            )
            db.session.commit()
            
            flash('Welcome back!', 'success')
            return redirect(url_for('dashboard.index'))
        else:
            flash('Invalid code. Try again.', 'error')
    
    return render_template('mfa/verify.html', email=user.email)
