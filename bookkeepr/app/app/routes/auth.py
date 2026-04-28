"""Authentication Routes"""
from flask import Blueprint, render_template, redirect, url_for, flash, request, session
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.exceptions import BadRequest
from extensions import limiter

bp = Blueprint('auth', __name__)


@bp.route('/login', methods=['GET', 'POST'])
@limiter.limit('20 per minute; 5 per second')
def login():
    """Login page"""
    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')
        
        # Input validation
        if not email:
            flash('Email is required', 'error')
            return render_template('auth/login.html')
        
        if '@' not in email or '.' not in email.split('@')[-1]:
            flash('Please enter a valid email address', 'error')
            return render_template('auth/login.html')
        
        if not password:
            flash('Password is required', 'error')
            return render_template('auth/login.html')
        
        if len(password) < 6:
            flash('Password must be at least 6 characters', 'error')
            return render_template('auth/login.html')
        
        # Check credentials
        from app.models.user import User
        user = User.query.filter_by(email=email).first()
        
        if user and user.check_password(password):
            if not user.is_active:
                flash('Your account has been deactivated. Please contact support.', 'error')
                return render_template('auth/login.html')
            
            # MFA check - redirect to verification if enabled
            if user.mfa_enabled and user.mfa_secret:
                session['mfa_pending_user_id'] = user.id
                session['mfa_pending_remember'] = request.form.get('remember_me') == 'on'
                return redirect(url_for('mfa.verify'))
            
            login_user(user, remember=request.form.get('remember_me') == 'on')
            user.last_login_at = __import__('datetime').datetime.utcnow()
            from extensions import db
            from app.models.audit_log import AuditLog
            
            # Audit log: successful login
            AuditLog.log(
                action='login',
                target_table='users',
                target_id=user.id,
                user=user,
                request=request,
            )
            db.session.commit()
            
            next_page = request.args.get('next')
            return redirect(next_page or url_for('main.index'))
        else:
            flash('Invalid email or password', 'error')
    
    return render_template('auth/login.html')


@bp.route('/logout')
@login_required
def logout():
    """Logout user"""
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('main.index'))


@bp.route('/register', methods=['GET', 'POST'])
@limiter.limit('10 per hour; 3 per minute')
def register():
    """Registration page"""
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')
        first_name = request.form.get('first_name', '').strip()
        last_name = request.form.get('last_name', '').strip()

        # Input validation
        errors = []

        if not email:
            errors.append('Email is required')
        elif '@' not in email or '.' not in email.split('@')[-1]:
            errors.append('Please enter a valid email address')

        if not password:
            errors.append('Password is required')
        elif len(password) < 8:
            errors.append('Password must be at least 8 characters')
        elif confirm_password and password != confirm_password:
            errors.append('Passwords do not match')

        if not first_name:
            errors.append('First name is required')
        
        if errors:
            for error in errors:
                flash(error, 'error')
            return render_template('auth/register.html')
        
        # Check if user exists
        from app.models.user import User
        from app.models.tenant import Tenant
        from app.models.audit_log import AuditLog
        from extensions import db
        
        existing = User.query.filter_by(email=email).first()
        if existing:
            flash('An account with this email already exists', 'error')
            return render_template('auth/register.html')
        
        # Create user (default role: operator)
        user = User(
            email=email,
            first_name=first_name,
            last_name=last_name,
            role='operator',  # Default new signups to operator role
        )
        user.set_password(password)
        db.session.add(user)
        db.session.flush()  # get user.id
        
        # Create tenant for this operator (Phase 1.1.3 - multi-tenancy)
        tenant = Tenant.create_for_user(user)
        user.tenant_id = tenant.id
        
        # Audit log
        AuditLog.log(
            action='register',
            target_table='users',
            target_id=user.id,
            user=user,
            tenant_id=tenant.id,
            new_value={'email': email, 'role': 'operator'},
            request=request,
        )
        
        db.session.commit()

        # Send welcome email (non-blocking)
        try:
            from app.services.email_service import send_welcome
            send_welcome(user)
        except Exception as _e:
            current_app.logger.warning('Welcome email failed: %s', _e)

        flash(f'Account created! Welcome, {first_name}. Your 14-day trial has started.', 'success')
        return redirect(url_for('auth.login'))
    
    return render_template('auth/register.html')


def _get_serializer():
    from itsdangerous import URLSafeTimedSerializer
    from flask import current_app
    return URLSafeTimedSerializer(current_app.config['SECRET_KEY'], salt='pw-reset')


@bp.route('/forgot-password', methods=['GET', 'POST'])
@limiter.limit('5 per hour')
def forgot_password():
    """Password reset request"""
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        if not email:
            flash('Email is required.', 'error')
            return render_template('auth/forgot_password.html')

        from app.models.user import User
        user = User.query.filter_by(email=email).first()

        if user:
            token = _get_serializer().dumps(user.id)
            reset_url = url_for('auth.reset_password', token=token, _external=True)
            try:
                from app.services.email_service import send_password_reset
                send_password_reset(user, reset_url)
            except Exception as _e:
                # Always log the link as fallback so dev/ops can use it
                current_app.logger.warning('[PASSWORD RESET LINK] %s — email error: %s', reset_url, _e)

        # Identical message whether email exists or not — prevents enumeration
        flash('If that email is registered, a reset link is on its way.', 'info')
        return redirect(url_for('auth.login'))

    return render_template('auth/forgot_password.html')


@bp.route('/reset-password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    """Reset password using a signed token"""
    from itsdangerous import BadSignature, SignatureExpired

    try:
        user_id = _get_serializer().loads(token, max_age=3600)
    except SignatureExpired:
        flash('This reset link has expired. Please request a new one.', 'error')
        return redirect(url_for('auth.forgot_password'))
    except BadSignature:
        flash('Invalid reset link.', 'error')
        return redirect(url_for('auth.forgot_password'))

    from app.models.user import User
    from extensions import db

    user = User.query.get(user_id)
    if not user:
        flash('User not found.', 'error')
        return redirect(url_for('auth.forgot_password'))

    if request.method == 'POST':
        password = request.form.get('password', '')
        confirm = request.form.get('confirm_password', '')

        if len(password) < 8:
            flash('Password must be at least 8 characters.', 'error')
            return render_template('auth/reset_password.html', token=token)

        if password != confirm:
            flash('Passwords do not match.', 'error')
            return render_template('auth/reset_password.html', token=token)

        user.set_password(password)
        db.session.commit()
        flash('Password updated! You can now log in.', 'success')
        return redirect(url_for('auth.login'))

    return render_template('auth/reset_password.html', token=token)
