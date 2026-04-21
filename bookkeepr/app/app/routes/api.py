"""API Routes"""
from flask import Blueprint, jsonify, request
from flask_login import login_required, current_user

from app import db
from app.models.transaction import Transaction
from app.models.account import Account
from app.models.company import Company

bp = Blueprint('api', __name__)


@bp.route('/health')
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'service': 'BookKeepr AI'
    })


@bp.route('/login', methods=['POST'])
def api_login():
    """API login endpoint for frontend"""
    from app.models.user import User
    from flask_login import login_user
    
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')
    
    user = User.query.filter_by(email=email).first()
    if user and user.check_password(password):
        login_user(user)
        return jsonify({
            'success': True,
            'user': user.to_dict()
        })
    
    return jsonify({
        'success': False,
        'error': 'Invalid credentials'
    }), 401


@bp.route('/user', methods=['GET'])
@login_required
def get_user():
    """Get current user info"""
    return jsonify(current_user.to_dict())


@bp.route('/companies', methods=['GET'])
@login_required
def list_companies():
    """List user's companies"""
    companies = Company.query.filter_by(user_id=current_user.id).all()
    return jsonify({
        'companies': [c.to_dict() for c in companies],
        'total': len(companies)
    })


@bp.route('/transactions', methods=['GET'])
@login_required
def list_transactions():
    """List transactions"""
    # Get first company for user
    company = Company.query.filter_by(user_id=current_user.id).first()
    if not company:
        return jsonify({
            'transactions': [],
            'total': 0,
            'page': 1,
            'per_page': 20
        })
    
    transactions = Transaction.query.filter_by(company_id=company.id).limit(50).all()
    return jsonify({
        'transactions': [t.to_dict() for t in transactions],
        'total': len(transactions),
        'page': 1,
        'per_page': 20
    })


@bp.route('/companies/<int:company_id>/transactions', methods=['GET'])
@login_required
def get_company_transactions(company_id):
    """Get transactions for a specific company"""
    from app.models.company import Company
    from app.models.transaction import Transaction
    
    # Verify company belongs to user
    company = Company.query.filter_by(id=company_id, user_id=current_user.id).first()
    if not company:
        return jsonify({'error': 'Company not found'}), 404
    
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 25, type=int)
    
    # Query transactions
    query = Transaction.query.filter_by(company_id=company_id)
    
    total = query.count()
    transactions = query.order_by(Transaction.transaction_date.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    return jsonify({
        'transactions': [t.to_dict() for t in transactions.items],
        'total': total,
        'pages': transactions.pages,
        'current_page': page
    })


@bp.route('/accounts', methods=['GET'])
@login_required
def list_accounts():
    """List accounts"""
    return jsonify({
        'accounts': [],
        'total': 0
    })


@bp.route('/sync', methods=['POST'])
@login_required
def trigger_sync():
    """Trigger data sync"""
    return jsonify({
        'status': 'started',
        'message': 'Sync initiated'
    })
