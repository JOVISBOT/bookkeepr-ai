"""Authentication Routes"""
from flask import Blueprint, render_template, redirect, url_for, flash, request, session
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.exceptions import BadRequest

bp = Blueprint('auth', __name__)


@bp.route('/login', methods=['GET', 'POST'])
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
def register():
    """Registration page"""
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
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
        
        flash(f'Account created! Welcome, {first_name}. Your 14-day trial has started.', 'success')
        return redirect(url_for('auth.login'))
    
    return render_template('auth/register.html')


@bp.route('/forgot-password')
def forgot_password():
    """Password reset request"""
    return render_template('auth/forgot_password.html')
