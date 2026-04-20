"""
API routes - REST endpoints for AJAX and integrations
"""
from flask import Blueprint, jsonify, request
from flask_login import login_required, current_user

from ..models import Company, Transaction

api_bp = Blueprint('api', __name__)


@api_bp.route('/companies')
@login_required
def list_companies():
    """List user's companies."""
    companies = Company.query.filter_by(user_id=current_user.id).all()
    return jsonify({
        'companies': [c.to_dict() for c in companies]
    })


@api_bp.route('/companies/<int:company_id>/transactions')
@login_required
def company_transactions(company_id):
    """Get transactions for a company."""
    # Verify ownership
    company = Company.query.filter_by(
        id=company_id,
        user_id=current_user.id
    ).first_or_404()
    
    page = request.args.get('page', 1, type=int)
    per_page = min(request.args.get('per_page', 50, type=int), 100)
    
    transactions = Transaction.query.filter_by(
        company_id=company_id
    ).order_by(
        Transaction.date.desc()
    ).paginate(page=page, per_page=per_page, error_out=False)
    
    return jsonify({
        'transactions': [t.to_dict() for t in transactions.items],
        'total': transactions.total,
        'pages': transactions.pages,
        'current_page': page
    })


@api_bp.route('/stats')
@login_required
def dashboard_stats():
    """Get dashboard statistics."""
    companies = Company.query.filter_by(user_id=current_user.id).all()
    
    total_transactions = 0
    uncategorized = 0
    categorized = 0
    
    for company in companies:
        total = company.transactions.count()
        uncategorized += company.transactions.filter_by(status='imported').count()
        categorized += company.transactions.filter(
            Transaction.status.in_(['categorized', 'reviewed'])
        ).count()
        total_transactions += total
    
    return jsonify({
        'companies': len(companies),
        'total_transactions': total_transactions,
        'uncategorized': uncategorized,
        'categorized': categorized,
        'categorization_rate': round(categorized / total_transactions * 100, 1) if total_transactions > 0 else 0
    })
