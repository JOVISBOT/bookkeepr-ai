"""
Transaction routes - list, categorize, review
"""
from flask import Blueprint, render_template, request, jsonify, flash
from flask_login import login_required, current_user

from ..extensions import db
from ..models import Transaction, Company

transactions_bp = Blueprint('transactions', __name__)


@transactions_bp.route('/')
@login_required
def list_transactions():
    """List transactions with filtering."""
    page = request.args.get('page', 1, type=int)
    company_id = request.args.get('company_id', type=int)
    status = request.args.get('status')
    
    # Get user's companies
    user_companies = Company.query.filter_by(user_id=current_user.id).all()
    company_ids = [c.id for c in user_companies]
    
    # Build query
    query = Transaction.query.filter(Transaction.company_id.in_(company_ids))
    
    if company_id and company_id in company_ids:
        query = query.filter_by(company_id=company_id)
    
    if status:
        query = query.filter_by(status=status)
    
    # Paginate
    transactions = query.order_by(Transaction.date.desc()).paginate(
        page=page, per_page=50, error_out=False
    )
    
    return render_template('transactions/list.html',
                         transactions=transactions,
                         companies=user_companies,
                         selected_company=company_id,
                         selected_status=status)


@transactions_bp.route('/review')
@login_required
def review_queue():
    """Show transactions needing review."""
    # Get user's companies
    user_companies = Company.query.filter_by(user_id=current_user.id).all()
    company_ids = [c.id for c in user_companies]
    
    # Get uncategorized transactions
    transactions = Transaction.query.filter(
        Transaction.company_id.in_(company_ids),
        Transaction.status.in_(['imported', 'suggested'])
    ).order_by(
        Transaction.category_confidence.desc(),
        Transaction.date.desc()
    ).limit(100).all()
    
    return render_template('transactions/review.html', transactions=transactions)


@transactions_bp.route('/<int:transaction_id>/categorize', methods=['POST'])
@login_required
def categorize_transaction(transaction_id):
    """Categorize a transaction."""
    transaction = Transaction.query.get_or_404(transaction_id)
    
    # Verify ownership
    company = Company.query.filter_by(
        id=transaction.company_id,
        user_id=current_user.id
    ).first()
    
    if not company:
        return jsonify({'error': 'Not authorized'}), 403
    
    category = request.json.get('category')
    
    if not category:
        return jsonify({'error': 'Category required'}), 400
    
    transaction.confirm_category(category)
    db.session.commit()
    
    return jsonify({
        'success': True,
        'transaction_id': transaction_id,
        'category': category
    })
