"""API Routes"""
from flask import Blueprint, jsonify, request
from flask_login import login_required, current_user
from werkzeug.exceptions import BadRequest

from extensions import db
from app.models.transaction import Transaction
from app.models.account import Account
from app.models.company import Company

bp = Blueprint('api', __name__)


def validate_json(*required_fields):
    """Decorator to validate JSON request body"""
    from functools import wraps
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            if not request.is_json:
                return jsonify({'success': False, 'error': 'Content-Type must be application/json'}), 400
            data = request.get_json()
            if data is None:
                return jsonify({'success': False, 'error': 'Invalid JSON body'}), 400
            missing = [field for field in required_fields if field not in data or data[field] in (None, '', [])]
            if missing:
                return jsonify({'success': False, 'error': f'Missing required fields: {", ".join(missing)}'}), 422
            return f(*args, **kwargs)
        return wrapper
    return decorator


def validate_query_params(**validators):
    """Decorator to validate query parameters"""
    from functools import wraps
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            errors = {}
            for param, validator in validators.items():
                value = request.args.get(param)
                if value is not None:
                    try:
                        validator(value)
                    except ValueError as e:
                        errors[param] = str(e)
            if errors:
                return jsonify({'success': False, 'error': 'Invalid query parameters', 'details': errors}), 422
            return f(*args, **kwargs)
        return wrapper
    return decorator


@bp.errorhandler(BadRequest)
def handle_bad_request(e):
    return jsonify({'success': False, 'error': 'Bad request', 'message': str(e)}), 400


@bp.after_request
def close_db_session(response):
    """Ensure database session is closed after each request"""
    try:
        db.session.close()
    except:
        pass
    return response


@bp.route('/health')
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'service': 'BookKeepr AI'
    })


@bp.route('/login', methods=['POST'])
@validate_json('email', 'password')
def api_login():
    """API login endpoint for frontend"""
    from app.models.user import User
    from flask_login import login_user
    
    data = request.get_json()
    email = data.get('email', '').strip().lower()
    password = data.get('password', '')
    
    if not email or '@' not in email:
        return jsonify({'success': False, 'error': 'Valid email required'}), 422
    
    if len(password) < 6:
        return jsonify({'success': False, 'error': 'Password must be at least 6 characters'}), 422
    
    user = User.query.filter_by(email=email).first()
    if user and user.check_password(password):
        if not user.is_active:
            return jsonify({'success': False, 'error': 'Account is deactivated'}), 403
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
@validate_query_params(
    page=lambda v: int(v) if int(v) > 0 else (_ for _ in ()).throw(ValueError('Page must be positive')),
    per_page=lambda v: int(v) if 1 <= int(v) <= 100 else (_ for _ in ()).throw(ValueError('Per page must be 1-100'))
)
def get_company_transactions(company_id):
    """Get transactions for a specific company"""
    from app.models.company import Company
    from app.models.transaction import Transaction
    
    # Verify company belongs to user
    company = Company.query.filter_by(id=company_id, user_id=current_user.id).first()
    if not company:
        return jsonify({'success': False, 'error': 'Company not found'}), 404
    
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 25, type=int)
    
    # Query transactions
    query = Transaction.query.filter_by(company_id=company_id)
    
    total = query.count()
    transactions = query.order_by(Transaction.transaction_date.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    return jsonify({
        'success': True,
        'transactions': [t.to_dict() for t in transactions.items],
        'total': total,
        'pages': transactions.pages,
        'current_page': page
    })


@bp.route('/accounts', methods=['GET'])
@login_required
def list_accounts():
    """List unique account names from transactions"""
    company = Company.query.filter_by(user_id=current_user.id).first()
    if not company:
        return jsonify({'accounts': [], 'total': 0})
    
    # Get distinct accounts from transactions
    rows = db.session.query(Transaction.account_name).filter(
        Transaction.company_id == company.id,
        Transaction.account_name.isnot(None),
    ).distinct().order_by(Transaction.account_name).all()
    accounts = [r[0] for r in rows if r[0]]
    return jsonify({'accounts': accounts, 'total': len(accounts)})


@bp.route('/categories', methods=['GET'])
@login_required
def list_categories():
    """List unique categories from transactions (or fallback to common ones)"""
    company = Company.query.filter_by(
        user_id=current_user.id, is_active=True, is_connected=True
    ).first() or Company.query.filter_by(user_id=current_user.id).first()
    
    common_categories = [
        'Advertising & Marketing', 'Bank Fees', 'Cost of Goods Sold',
        'Insurance', 'Meals & Entertainment', 'Office Supplies',
        'Payroll', 'Professional Services', 'Rent & Lease',
        'Software & Subscriptions', 'Taxes', 'Travel',
        'Utilities', 'Sales Revenue', 'Service Revenue', 'Interest Income',
        'Uncategorized'
    ]
    
    if not company:
        return jsonify({'categories': common_categories, 'total': len(common_categories)})
    
    rows = db.session.query(Transaction.category).filter(
        Transaction.company_id == company.id,
        Transaction.category.isnot(None),
    ).distinct().order_by(Transaction.category).all()
    custom = [r[0] for r in rows if r[0]]
    
    # Merge custom + common, custom first
    seen = set()
    categories = []
    for c in custom + common_categories:
        if c not in seen:
            categories.append(c)
            seen.add(c)
    return jsonify({'categories': categories, 'total': len(categories)})


@bp.route('/vendors', methods=['GET'])
@login_required
def list_vendors():
    """List unique vendors"""
    company = Company.query.filter_by(user_id=current_user.id).first()
    if not company:
        return jsonify({'vendors': [], 'total': 0})
    
    rows = db.session.query(Transaction.vendor_name).filter(
        Transaction.company_id == company.id,
        Transaction.vendor_name.isnot(None),
    ).distinct().order_by(Transaction.vendor_name).all()
    vendors = [r[0] for r in rows if r[0]]
    return jsonify({'vendors': vendors, 'total': len(vendors)})


@bp.route('/sync', methods=['POST'])
@login_required
def trigger_sync():
    """Trigger data sync"""
    company = Company.query.filter_by(user_id=current_user.id).first()
    if not company:
        return jsonify({'success': False, 'error': 'No company connected'}), 404
    
    # Update sync status
    company.sync_status = 'syncing'
    db.session.commit()
    
    return jsonify({
        'success': True,
        'status': 'started',
        'message': 'Sync initiated',
        'company_id': company.id
    })
