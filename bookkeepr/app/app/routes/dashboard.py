"""Dashboard Routes"""
from flask import Blueprint, render_template, flash, current_app, jsonify
from flask_login import login_required, current_user
from app.models.company import Company
from app.models.transaction import Transaction
from app.services.ai_categorization import get_categorization_service, categorize_all_pending

bp = Blueprint('dashboard', __name__)


@bp.route('/')
@login_required
def index():
    """Main dashboard"""
    # Fetch real stats for the template
    company = Company.query.filter_by(user_id=current_user.id).first()
    stats = {}
    transactions = []
    if company:
        stats = {
            'total_transactions': Transaction.query.filter_by(company_id=company.id).count(),
            'month_transactions': Transaction.query.filter_by(company_id=company.id).count(),  # Simplified
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

    return render_template('dashboard/index.html', company=company, stats=stats, transactions=transactions)


@bp.route('/transactions')
@login_required
def transactions():
    """Transaction list"""
    return render_template('dashboard/transactions.html')


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
    result = categorize_all_pending(company.id)
    return jsonify(result)
