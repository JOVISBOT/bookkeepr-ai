"""Dashboard Routes"""
from flask import Blueprint, render_template, flash, current_app, jsonify
from flask_login import login_required, current_user
from app.models.company import Company
from app.models.transaction import Transaction
from app.models.subscription import UserSubscription
from app.services.ai_categorization import get_ai_categorization_service, get_learning_system

bp = Blueprint('dashboard', __name__)


@bp.route('/')
@login_required
def index():
    """Main dashboard with premium features"""
    from flask import request
    
    # All active clients for this user (for selector)
    all_clients = Company.query.filter_by(
        user_id=current_user.id,
        is_active=True,
    ).order_by(Company.qbo_company_name).all()
    
    # Selected client (via ?client_id= or default to first connected)
    selected_id = request.args.get('client_id', type=int)
    company = None
    if selected_id:
        company = Company.query.filter_by(id=selected_id, user_id=current_user.id).first()
    if not company:
        # Prefer connected company
        company = Company.query.filter_by(
            user_id=current_user.id,
            is_active=True,
            is_connected=True,
        ).first()
    if not company:
        company = all_clients[0] if all_clients else None
    
    # Get subscription
    subscription = UserSubscription.query.filter_by(user_id=current_user.id).first()
    
    stats = {}
    transactions = []
    if company:
        stats = {
            'total_transactions': Transaction.query.filter_by(company_id=company.id).count(),
            'month_transactions': Transaction.query.filter_by(company_id=company.id).count(),
            'uncategorized_count': Transaction.query.filter_by(
                company_id=company.id, categorization_status='uncategorized'
            ).count(),
            'pending_count': Transaction.query.filter_by(
                company_id=company.id, review_status='pending'
            ).count(),
            'auto_categorized_count': Transaction.query.filter_by(
                company_id=company.id, categorized_by='ai'
            ).count(),
            'auto_categorization_rate': 0,
            'last_sync_at': company.last_sync_at,
        }
        if stats['total_transactions'] > 0:
            stats['auto_categorization_rate'] = round(
                (stats['auto_categorized_count'] / stats['total_transactions']) * 100, 1
            )
        transactions = Transaction.query.filter_by(company_id=company.id).order_by(
            Transaction.transaction_date.desc()
        ).limit(10).all()

    return render_template('dashboard/index.html', 
        company=company, 
        all_clients=all_clients,
        stats=stats, 
        transactions=transactions,
        subscription=subscription
    )


@bp.route('/transactions')
@login_required
def transactions():
    """Transaction list - actually load data"""
    from flask import request
    
    # Pick connected company or first active
    company = Company.query.filter_by(
        user_id=current_user.id,
        is_active=True,
        is_connected=True,
    ).first()
    if not company:
        company = Company.query.filter_by(user_id=current_user.id, is_active=True).first()
    
    transactions_list = []
    total = 0
    if company:
        # Apply filters from query string
        q = Transaction.query.filter_by(company_id=company.id)
        
        search = request.args.get('search', '').strip()
        if search:
            q = q.filter(Transaction.description.ilike(f'%{search}%'))
        
        category_filter = request.args.get('category', '').strip()
        if category_filter == 'uncategorized':
            q = q.filter_by(categorization_status='uncategorized')
        elif category_filter == 'categorized':
            q = q.filter(Transaction.categorization_status != 'uncategorized')
        
        status_filter = request.args.get('status', '').strip()
        if status_filter == 'needs_review':
            q = q.filter_by(review_status='pending')
        elif status_filter == 'approved':
            q = q.filter_by(review_status='approved')
        
        total = q.count()
        transactions_list = q.order_by(Transaction.transaction_date.desc()).limit(200).all()
    
    return render_template('dashboard/transactions.html',
                           transactions=transactions_list,
                           total=total,
                           company=company)


@bp.route('/transactions/<int:transaction_id>')
@login_required
def transaction_detail(transaction_id):
    """Transaction detail view"""
    return render_template('dashboard/transaction_detail.html', transaction_id=transaction_id)


@bp.route('/accounts')
@login_required
def accounts():
    """Chart of accounts"""
    return render_template('dashboard/accounts.html')


@bp.route('/reports')
@login_required
def reports():
    """Reports page"""
    return render_template('dashboard/reports.html')


@bp.route('/settings')
@login_required
def settings():
    """User settings"""
    return render_template('dashboard/settings.html')


@bp.route('/settings/company')
@login_required
def company_settings():
    """Company/QBO connection settings"""
    return render_template('dashboard/company_settings.html')


@bp.route('/ai-categorize', methods=['POST'])
@login_required
def ai_categorize():
    """AJAX endpoint: run AI categorization on all pending transactions."""
    company = Company.query.filter_by(user_id=current_user.id).first()
    if not company:
        return jsonify({'success': False, 'error': 'No company found'}), 404
    service = get_ai_categorization_service()
    result = service.categorize_batch(company.id)
    return jsonify(result)
