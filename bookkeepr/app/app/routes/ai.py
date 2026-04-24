"""
AI Routes for BookKeepr
Auto-categorization and intelligent features
"""
from flask import Blueprint, jsonify, request
from flask_login import login_required, current_user
from app.models.transaction import Transaction
from app.models.company import Company

bp = Blueprint('ai', __name__, url_prefix='/api/v1/ai')

@bp.route('/categorize', methods=['POST'])
@login_required
def categorize_transactions():
    """AI auto-categorize transactions"""
    from ai_categorization import categorizer
    
    # Get user's companies
    companies = Company.query.filter_by(user_id=current_user.id).all()
    company_ids = [c.id for c in companies]
    
    # Get uncategorized transactions
    transactions = Transaction.query.filter(
        Transaction.company_id.in_(company_ids),
        Transaction.category == None
    ).all()
    
    if not transactions:
        return jsonify({
            'message': 'No uncategorized transactions found',
            'categorized': 0
        })
    
    # Categorize each transaction
    results = []
    categorized_count = 0
    
    for transaction in transactions:
        category = categorizer.categorize(
            transaction.description,
            transaction.amount
        )
        
        if category and category != 'Uncategorized':
            transaction.category = category
            categorized_count += 1
            
        results.append({
            'id': transaction.id,
            'description': transaction.description,
            'amount': float(transaction.amount),
            'category': category,
            'date': transaction.date.isoformat() if transaction.date else None
        })
    
    # Save changes
    from extensions import db
    db.session.commit()
    
    return jsonify({
        'message': f'Successfully categorized {categorized_count} transactions',
        'categorized': categorized_count,
        'total': len(transactions),
        'results': results
    })

@bp.route('/suggestions', methods=['GET'])
@login_required
def get_suggestions():
    """Get AI suggestions for uncategorized transactions"""
    from ai_categorization import categorizer
    
    companies = Company.query.filter_by(user_id=current_user.id).all()
    company_ids = [c.id for c in companies]
    
    transactions = Transaction.query.filter(
        Transaction.company_id.in_(company_ids),
        Transaction.category == None
    ).limit(10).all()
    
    suggestions = []
    for transaction in transactions:
        category = categorizer.categorize(
            transaction.description,
            transaction.amount
        )
        suggestions.append({
            'id': transaction.id,
            'description': transaction.description,
            'suggested_category': category,
            'confidence': 0.85 if category != 'Uncategorized' else 0.3,
            'amount': float(transaction.amount)
        })
    
    return jsonify({
        'suggestions': suggestions,
        'count': len(suggestions)
    })

@bp.route('/stats', methods=['GET'])
@login_required
def get_ai_stats():
    """Get AI categorization statistics"""
    companies = Company.query.filter_by(user_id=current_user.id).all()
    company_ids = [c.id for c in companies]
    
    total = Transaction.query.filter(
        Transaction.company_id.in_(company_ids)
    ).count()
    
    categorized = Transaction.query.filter(
        Transaction.company_id.in_(company_ids),
        Transaction.category != None
    ).count()
    
    uncategorized = total - categorized
    
    return jsonify({
        'total_transactions': total,
        'categorized': categorized,
        'uncategorized': uncategorized,
        'percentage': (categorized / total * 100) if total > 0 else 0
    })
