"""
Dashboard routes - main application UI
"""
from flask import Blueprint, render_template
from flask_login import login_required, current_user

from ..models import Company, Transaction

dashboard_bp = Blueprint('dashboard', __name__)


@dashboard_bp.route('/')
@login_required
def index():
    """Main dashboard."""
    # Get user's companies
    companies = Company.query.filter_by(
        user_id=current_user.id,
        is_active=True
    ).all()
    
    # Get stats
    total_transactions = 0
    uncategorized_count = 0
    
    for company in companies:
        total_transactions += company.transactions.count()
        uncategorized_count += company.transactions.filter_by(
            status='imported'
        ).count()
    
    # Recent transactions
    recent_transactions = []
    if companies:
        company_ids = [c.id for c in companies]
        recent_transactions = Transaction.query.filter(
            Transaction.company_id.in_(company_ids)
        ).order_by(
            Transaction.created_at.desc()
        ).limit(10).all()
    
    return render_template('dashboard.html',
                         companies=companies,
                         total_transactions=total_transactions,
                         uncategorized_count=uncategorized_count,
                         recent_transactions=recent_transactions)


@dashboard_bp.route('/companies')
@login_required
def companies():
    """List all companies."""
    companies = Company.query.filter_by(user_id=current_user.id).all()
    return render_template('companies.html', companies=companies)
