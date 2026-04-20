"""
Authentication routes - OAuth and login
"""
from flask import Blueprint, render_template, redirect, url_for, request, flash, session
from flask_login import login_user, logout_user, login_required, current_user

from ..extensions import db
from ..models import User, Company
from ..services.qb_service import QuickBooksService

auth_bp = Blueprint('auth', __name__, template_folder='../templates/auth')


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """User login."""
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.index'))
    
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        remember = request.form.get('remember', False)
        
        user = User.query.filter_by(email=email).first()
        
        if user and user.check_password(password):
            if not user.is_active:
                flash('Account is disabled.', 'error')
                return render_template('auth/login.html')
            
            login_user(user, remember=remember)
            next_page = request.args.get('next')
            flash(f'Welcome back, {user.first_name or user.email}!', 'success')
            return redirect(next_page or url_for('dashboard.index'))
        else:
            flash('Invalid email or password.', 'error')
    
    return render_template('auth/login.html')


@auth_bp.route('/logout')
@login_required
def logout():
    """User logout."""
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('auth.login'))


@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    """User registration."""
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.index'))
    
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')
        first_name = request.form.get('first_name', '').strip()
        last_name = request.form.get('last_name', '').strip()
        
        # Validation
        errors = []
        if not email or '@' not in email:
            errors.append('Valid email is required.')
        if len(password) < 8:
            errors.append('Password must be at least 8 characters.')
        if password != confirm_password:
            errors.append('Passwords do not match.')
        
        # Check existing
        if User.query.filter_by(email=email).first():
            errors.append('Email already registered.')
        
        if errors:
            for error in errors:
                flash(error, 'error')
            return render_template('auth/register.html')
        
        # Create user
        user = User(
            email=email,
            password=password,
            first_name=first_name,
            last_name=last_name
        )
        db.session.add(user)
        db.session.commit()
        
        flash('Registration successful! Please log in.', 'success')
        return redirect(url_for('auth.login'))
    
    return render_template('auth/register.html')


# QuickBooks OAuth Routes

@auth_bp.route('/qbo/connect')
@login_required
def qbo_connect():
    """Start QuickBooks OAuth flow."""
    qb_service = QuickBooksService()
    auth_url = qb_service.get_authorization_url()
    return redirect(auth_url)


@auth_bp.route('/qbo/callback')
@login_required
def qbo_callback():
    """Handle OAuth callback from QuickBooks."""
    auth_code = request.args.get('code')
    realm_id = request.args.get('realmId')
    error = request.args.get('error')
    
    if error:
        flash(f'QuickBooks authorization error: {error}', 'error')
        return redirect(url_for('dashboard.index'))
    
    if not auth_code or not realm_id:
        flash('Authorization failed. Please try again.', 'error')
        return redirect(url_for('dashboard.index'))
    
    # Exchange code for tokens
    qb_service = QuickBooksService()
    token_data = qb_service.exchange_code_for_tokens(auth_code, realm_id)
    
    if not token_data:
        flash('Failed to connect to QuickBooks. Please try again.', 'error')
        return redirect(url_for('dashboard.index'))
    
    # Get company info from QBO
    temp_company = Company(
        id=0,  # Temporary, won't be saved
        realm_id=realm_id,
        access_token=token_data['access_token'],
        refresh_token=token_data['refresh_token']
    )
    qb_service.company = temp_company
    
    company_info = qb_service.get_company_info()
    company_name = company_info.get('CompanyInfo', {}).get('CompanyName', 'Unknown Company') if company_info else 'Unknown Company'
    
    # Check if company already exists for this user
    existing = Company.query.filter_by(
        user_id=current_user.id,
        realm_id=realm_id
    ).first()
    
    if existing:
        # Update tokens
        existing.update_tokens(
            access_token=token_data['access_token'],
            refresh_token=token_data['refresh_token'],
            expires_in=token_data['expires_in']
        )
        existing.company_name = company_name
        existing.is_active = True
        flash(f'QuickBooks connection updated for {company_name}.', 'success')
    else:
        # Create new company
        company = Company(
            user_id=current_user.id,
            realm_id=realm_id,
            company_name=company_name,
            is_sandbox=True  # Will detect from config
        )
        company.update_tokens(
            access_token=token_data['access_token'],
            refresh_token=token_data['refresh_token'],
            expires_in=token_data['expires_in']
        )
        db.session.add(company)
        db.session.flush()  # Get ID
        
        # Create default categories
        QuickBooksService.create_default_categories(company.id)
        
        flash(f'QuickBooks connected successfully: {company_name}', 'success')
    
    db.session.commit()
    return redirect(url_for('dashboard.index'))


@auth_bp.route('/qbo/disconnect/<int:company_id>')
@login_required
def qbo_disconnect(company_id):
    """Disconnect QuickBooks company."""
    company = Company.query.filter_by(
        id=company_id,
        user_id=current_user.id
    ).first_or_404()
    
    company.is_active = False
    company.access_token = None
    company.refresh_token = None
    db.session.commit()
    
    flash(f'Disconnected from {company.company_name}.', 'info')
    return redirect(url_for('dashboard.index'))
