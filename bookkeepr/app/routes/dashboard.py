"""
Dashboard Routes - Main UI
"""
from flask import Blueprint, render_template, jsonify, request, session
from flask_login import login_required, current_user
from app import db
from app.models.company import Company
from app.models.transaction import Transaction
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)
dashboard_bp = Blueprint('dashboard', __name__)


@dashboard_bp.route('/')
@login_required
def index():
    """
    Main dashboard - show company overview with transactions
    """
    # Get user's company (for now, get first one)
    company = Company.query.filter_by(user_id=current_user.id).first()
    
    if not company:
        # No company connected yet
        return render_template('dashboard/index.html',
                             company=None,
                             qb_connected=False,
                             stats=None,
                             transactions=None,
                             pagination=None)
    
    # Get page number from query params
    page = request.args.get('page', 1, type=int)
    per_page = 25
    
    # Get paginated transactions
    pagination = Transaction.query.filter_by(company_id=company.id)\
        .order_by(Transaction.transaction_date.desc())\
        .paginate(page=page, per_page=per_page, error_out=False)
    
    transactions = pagination.items
    
    # Calculate stats
    stats = get_company_stats(company.id)
    
    return render_template('dashboard/index.html',
                         company=company,
                         qb_connected=company.is_connected,
                         stats=stats,
                         transactions=transactions,
                         pagination=pagination)


@dashboard_bp.route('/company/<int:company_id>')
@login_required
def company_detail(company_id):
    """
    Company detail view with transactions
    """
    company = Company.query.get_or_404(company_id)
    
    # Ensure user owns this company
    if company.user_id != current_user.id:
        return jsonify({'error': 'Unauthorized'}), 403
    
    # Get recent transactions
    transactions = Transaction.query.filter_by(company_id=company_id)\
        .order_by(Transaction.transaction_date.desc())\
        .limit(50).all()
    
    # Get pending review count
    pending_count = Transaction.query.filter_by(
        company_id=company_id,
        needs_review=True
    ).count()
    
    return render_template('dashboard/company.html',
                         company=company,
                         transactions=transactions,
                         pending_count=pending_count)


@dashboard_bp.route('/company/<int:company_id>/transactions')
@login_required
def transactions(company_id):
    """
    Transaction list view
    """
    company = Company.query.get_or_404(company_id)
    
    if company.user_id != current_user.id:
        return jsonify({'error': 'Unauthorized'}), 403
    
    # Filter options
    status = request.args.get('status', 'all')
    page = request.args.get('page', 1, type=int)
    per_page = 25
    
    query = Transaction.query.filter_by(company_id=company_id)
    
    if status == 'pending':
        query = query.filter_by(needs_review=True)
    elif status == 'categorized':
        query = query.filter(Transaction.category_id.isnot(None))
    elif status == 'uncategorized':
        query = query.filter(Transaction.category_id.is_(None))
    
    transactions = query.order_by(Transaction.transaction_date.desc())\
        .paginate(page=page, per_page=per_page)
    
    return render_template('dashboard/transactions.html',
                         company=company,
                         transactions=transactions,
                         status=status)


@dashboard_bp.route('/company/<int:company_id>/review')
@login_required
def review_queue(company_id):
    """
    Review queue - uncategorized transactions
    """
    company = Company.query.get_or_404(company_id)
    
    if company.user_id != current_user.id:
        return jsonify({'error': 'Unauthorized'}), 403
    
    # Get uncategorized transactions
    transactions = Transaction.get_uncategorized(company_id, limit=100)
    
    return render_template('dashboard/review.html',
                         company=company,
                         transactions=transactions)


def get_company_stats(company_id):
    """
    Get dashboard statistics for a company
    """
    from datetime import datetime, timedelta
    
    # Date ranges
    today = datetime.utcnow()
    month_start = today.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    
    # Basic counts
    total_transactions = Transaction.query.filter_by(company_id=company_id).count()
    pending_count = Transaction.query.filter_by(company_id=company_id, needs_review=True).count()
    uncategorized_count = Transaction.query.filter_by(
        company_id=company_id, 
        category_id=None
    ).count()
    
    # This month
    month_transactions = Transaction.query.filter(
        Transaction.company_id == company_id,
        Transaction.transaction_date >= month_start
    ).count()
    
    # Auto-categorization stats
    total_with_category = Transaction.query.filter(
        Transaction.company_id == company_id,
        Transaction.category_id.isnot(None)
    ).count()
    
    auto_categorized = Transaction.query.filter(
        Transaction.company_id == company_id,
        Transaction.ai_processed == True
    ).count()
    
    auto_rate = (auto_categorized / total_with_category * 100) if total_with_category > 0 else 0
    
    # Get company for last sync info
    company = Company.query.get(company_id)
    last_sync = company.last_sync_at if company else None
    
    return {
        'total_transactions': total_transactions,
        'pending_count': pending_count,
        'uncategorized_count': uncategorized_count,
        'month_transactions': month_transactions,
        'categorized_count': total_with_category,
        'auto_categorized_count': auto_categorized,
        'auto_categorization_rate': round(auto_rate, 1),
        'last_sync_at': last_sync.strftime('%Y-%m-%d %H:%M') if last_sync else 'Never'
    }


@dashboard_bp.route('/api/stats/<int:company_id>')
@login_required
def api_stats(company_id):
    """
    API endpoint for dashboard stats
    """
    company = Company.query.get_or_404(company_id)
    
    if company.user_id != current_user.id:
        return jsonify({'error': 'Unauthorized'}), 403
    
    stats = get_company_stats(company_id)
    return jsonify(stats)


@dashboard_bp.route('/sync')
def sync_page():
    """Sync page - temporarily without login"""
    return render_template('dashboard/sync.html')