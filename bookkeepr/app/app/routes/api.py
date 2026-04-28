"""API Routes"""
from datetime import datetime
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
    """Health check — used by Render and uptime monitors."""
    db_ok = True
    try:
        db.session.execute(db.text('SELECT 1'))
    except Exception:
        db_ok = False
    return jsonify({
        'status': 'ok' if db_ok else 'degraded',
        'version': '1.0.0',
        'db': 'ok' if db_ok else 'error',
        'timestamp': datetime.utcnow().isoformat() + 'Z',
    }), 200 if db_ok else 503


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


@bp.route('/user/password', methods=['PUT'])
@login_required
def change_password():
    """Change current user's password"""
    from app.models.user import User
    from werkzeug.security import check_password_hash, generate_password_hash
    data = request.get_json() or {}
    current_pw = data.get('current_password', '')
    new_pw = data.get('new_password', '')
    if not current_pw or not new_pw:
        return jsonify({'success': False, 'error': 'Both current and new password are required'}), 422
    if len(new_pw) < 8:
        return jsonify({'success': False, 'error': 'New password must be at least 8 characters'}), 422
    user = User.query.get(current_user.id)
    if not user.password_hash or not check_password_hash(user.password_hash, current_pw):
        return jsonify({'success': False, 'error': 'Current password is incorrect'}), 403
    user.password_hash = generate_password_hash(new_pw)
    db.session.commit()
    return jsonify({'success': True})


@bp.route('/user/preferences', methods=['GET'])
@login_required
def get_preferences():
    """Get current user's preferences"""
    from app.models.user_preference import UserPreference
    prefs = UserPreference.query.filter_by(user_id=current_user.id).first()
    if not prefs:
        return jsonify({'success': True, 'preferences': {
            'auto_categorization': True,
            'confidence_threshold': 80,
            'notify_daily_summary': True,
            'notify_uncategorized': True,
            'notify_monthly_reports': False,
            'notify_anomalies': False,
        }})
    return jsonify({'success': True, 'preferences': {
        'auto_categorization': prefs.auto_categorization,
        'confidence_threshold': prefs.confidence_threshold,
        'notify_daily_summary': prefs.notify_daily_summary,
        'notify_uncategorized': prefs.notify_uncategorized,
        'notify_monthly_reports': prefs.notify_monthly_reports,
        'notify_anomalies': prefs.notify_anomalies,
    }})


@bp.route('/user/preferences', methods=['PUT'])
@login_required
def update_preferences():
    """Save current user's preferences"""
    from app.models.user_preference import UserPreference
    data = request.get_json() or {}
    prefs = UserPreference.query.filter_by(user_id=current_user.id).first()
    if not prefs:
        prefs = UserPreference(user_id=current_user.id)
        db.session.add(prefs)
    if 'auto_categorization' in data:
        prefs.auto_categorization = bool(data['auto_categorization'])
    if 'confidence_threshold' in data:
        val = int(data['confidence_threshold'])
        prefs.confidence_threshold = max(50, min(95, val))
    if 'notify_daily_summary' in data:
        prefs.notify_daily_summary = bool(data['notify_daily_summary'])
    if 'notify_uncategorized' in data:
        prefs.notify_uncategorized = bool(data['notify_uncategorized'])
    if 'notify_monthly_reports' in data:
        prefs.notify_monthly_reports = bool(data['notify_monthly_reports'])
    if 'notify_anomalies' in data:
        prefs.notify_anomalies = bool(data['notify_anomalies'])
    db.session.commit()
    return jsonify({'success': True})


@bp.route('/user/profile', methods=['PUT'])
@login_required
def update_profile():
    """Update current user's profile"""
    from app.models.user import User
    data = request.get_json() or {}
    user = User.query.get(current_user.id)
    if 'first_name' in data:
        user.first_name = data['first_name'].strip()
    if 'last_name' in data:
        user.last_name = data['last_name'].strip()
    if 'email' in data:
        email = data['email'].strip().lower()
        if email != user.email:
            existing = User.query.filter_by(email=email).first()
            if existing:
                return jsonify({'success': False, 'error': 'Email already in use'}), 409
            user.email = email
    db.session.commit()
    return jsonify({'success': True})


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

    company.sync_status = 'syncing'
    db.session.commit()

    return jsonify({
        'success': True,
        'status': 'started',
        'message': 'Sync initiated',
        'company_id': company.id
    })


# ============================================================================
# Company-scoped endpoints for React frontend
# ============================================================================

@bp.route('/companies/<int:company_id>/seed-accounts', methods=['POST'])
@login_required
def seed_company_accounts(company_id):
    """Seed GAAP chart of accounts + vendor knowledge for a company (idempotent)."""
    company = Company.query.filter_by(id=company_id, user_id=current_user.id).first()
    if not company:
        return jsonify({'success': False, 'error': 'Company not found'}), 404
    from app.services.gaap_coa import seed_gaap_accounts
    from app.services.vendor_seeds import seed_vendor_knowledge
    accounts = seed_gaap_accounts(company_id)
    vendors = seed_vendor_knowledge(company_id)
    return jsonify({'success': True, 'accounts': accounts, 'vendors': vendors})


@bp.route('/companies/<int:company_id>/accounts', methods=['GET'])
@login_required
def get_company_accounts(company_id):
    """Get accounts for a specific company"""
    company = Company.query.filter_by(id=company_id, user_id=current_user.id).first()
    if not company:
        return jsonify({'success': False, 'error': 'Company not found'}), 404

    account_type = request.args.get('type')
    query = Account.query.filter_by(company_id=company_id)
    if account_type:
        query = query.filter(Account.account_type.ilike(f'%{account_type}%'))

    accounts = query.order_by(Account.name).all()
    return jsonify([a.to_dict() for a in accounts])


@bp.route('/companies/<int:company_id>/review-queue', methods=['GET'])
@login_required
def get_company_review_queue(company_id):
    """Get transactions needing human review for a company"""
    company = Company.query.filter_by(id=company_id, user_id=current_user.id).first()
    if not company:
        return jsonify({'success': False, 'error': 'Company not found'}), 404

    status = request.args.get('status', 'pending')
    confidence = request.args.get('confidence')
    page = request.args.get('page', 1, type=int)
    limit = request.args.get('limit', 50, type=int)

    query = Transaction.query.filter_by(company_id=company_id)

    if status == 'pending':
        query = query.filter(
            db.or_(
                Transaction.review_status == 'pending',
                Transaction.categorization_status == 'suggested'
            )
        )
    elif status in ('approved', 'flagged'):
        query = query.filter(Transaction.review_status == status)

    if confidence == 'high':
        query = query.filter(Transaction.suggested_confidence >= 80)
    elif confidence == 'medium':
        query = query.filter(
            Transaction.suggested_confidence >= 50,
            Transaction.suggested_confidence < 80
        )
    elif confidence == 'low':
        query = query.filter(
            db.or_(
                Transaction.suggested_confidence < 50,
                Transaction.suggested_confidence.is_(None)
            )
        )

    total = query.count()
    paginated = query.order_by(Transaction.transaction_date.desc()).paginate(
        page=page, per_page=limit, error_out=False
    )

    return jsonify({
        'transactions': [t.to_dict() for t in paginated.items],
        'total': total,
        'pages': paginated.pages,
        'current_page': page
    })


@bp.route('/transactions/<int:transaction_id>/categorize', methods=['POST'])
@login_required
def categorize_transaction(transaction_id):
    """Manually categorize a transaction"""
    data = request.get_json() or {}
    account_id = data.get('account_id')

    transaction = Transaction.query.get(transaction_id)
    if not transaction:
        return jsonify({'success': False, 'error': 'Transaction not found'}), 404

    company = Company.query.filter_by(id=transaction.company_id, user_id=current_user.id).first()
    if not company:
        return jsonify({'success': False, 'error': 'Access denied'}), 403

    if account_id:
        account = Account.query.get(account_id)
        if account:
            transaction.category = account.name
            transaction.account_id = account_id
            transaction.account_name = account.name

    transaction.categorization_status = 'categorized'
    transaction.categorized_by = 'user'
    transaction.categorized_at = datetime.utcnow()
    transaction.review_status = 'approved'
    db.session.commit()

    return jsonify({'success': True, 'transaction': transaction.to_dict()})


@bp.route('/transactions/<int:transaction_id>/review', methods=['POST'])
@login_required
def review_transaction(transaction_id):
    """Approve, reject, or correct an AI categorization"""
    data = request.get_json() or {}
    action = data.get('action')  # approve, reject, correct
    account_id = data.get('account_id')
    notes = data.get('notes')

    if action not in ('approve', 'reject', 'correct'):
        return jsonify({'success': False, 'error': 'Invalid action'}), 400

    transaction = Transaction.query.get(transaction_id)
    if not transaction:
        return jsonify({'success': False, 'error': 'Transaction not found'}), 404

    company = Company.query.filter_by(id=transaction.company_id, user_id=current_user.id).first()
    if not company:
        return jsonify({'success': False, 'error': 'Access denied'}), 403

    now = datetime.utcnow()

    if action == 'approve':
        transaction.review_status = 'approved'
        if transaction.suggested_category and not transaction.category:
            transaction.category = transaction.suggested_category
        transaction.categorization_status = 'categorized'
    elif action == 'reject':
        transaction.review_status = 'flagged'
        transaction.categorization_status = 'uncategorized'
        transaction.category = None
    elif action == 'correct':
        transaction.review_status = 'approved'
        transaction.categorization_status = 'categorized'
        transaction.categorized_by = 'user'
        if account_id:
            account = Account.query.get(account_id)
            if account:
                transaction.category = account.name
                transaction.account_id = account_id
                transaction.account_name = account.name

    transaction.reviewed_by_user_id = current_user.id
    transaction.reviewed_at = now
    if notes:
        transaction.review_notes = notes

    db.session.commit()
    return jsonify({
        'success': True,
        'message': f'Transaction {action}d',
        'transaction': transaction.to_dict()
    })


@bp.route('/transactions/bulk-review', methods=['POST'])
@login_required
def bulk_review_transactions():
    """Bulk approve or correct multiple transactions"""
    data = request.get_json() or {}
    transaction_ids = data.get('transaction_ids', [])
    action = data.get('action')
    account_id = data.get('account_id')

    if not transaction_ids or action not in ('approve', 'correct'):
        return jsonify({'success': False, 'error': 'Invalid request'}), 400

    processed = 0
    errors = []
    now = datetime.utcnow()
    account = Account.query.get(account_id) if account_id else None

    for tid in transaction_ids:
        transaction = Transaction.query.get(tid)
        if not transaction:
            errors.append(f'Transaction {tid} not found')
            continue

        company = Company.query.filter_by(id=transaction.company_id, user_id=current_user.id).first()
        if not company:
            errors.append(f'Access denied for transaction {tid}')
            continue

        transaction.review_status = 'approved'
        transaction.categorization_status = 'categorized'
        transaction.reviewed_by_user_id = current_user.id
        transaction.reviewed_at = now

        if action == 'correct' and account:
            transaction.category = account.name
            transaction.account_id = account_id
            transaction.account_name = account.name
            transaction.categorized_by = 'user'
        elif action == 'approve' and transaction.suggested_category and not transaction.category:
            transaction.category = transaction.suggested_category

        processed += 1

    db.session.commit()
    return jsonify({
        'success': True,
        'processed': processed,
        'errors': errors,
        'message': f'{processed} transactions {action}d'
    })


@bp.route('/companies/<int:company_id>/ai-categorize', methods=['POST'])
@login_required
def run_ai_categorize(company_id):
    """Local classifier: uses transaction history first, GAAP rules as fallback. No API calls."""
    from app.services.local_classifier import classify as local_classify
    from app.services.gaap_coa import seed_gaap_accounts

    company = Company.query.filter_by(id=company_id, user_id=current_user.id).first()
    if not company:
        return jsonify({'success': False, 'error': 'Company not found'}), 404

    data = request.get_json() or {}
    limit = data.get('limit', 100)
    auto_approve = data.get('auto_approve_high_confidence', True)

    # Seed GAAP accounts once so the fallback has accounts to link to
    existing_gaap = Account.query.filter(
        Account.company_id == company_id,
        Account.qbo_account_id.like('gaap-%')
    ).count()
    if existing_gaap == 0:
        seed_gaap_accounts(company_id)

    gaap_accounts = {
        a.account_number: a
        for a in Account.query.filter(
            Account.company_id == company_id,
            Account.qbo_account_id.like('gaap-%')
        ).all()
    }

    transactions = Transaction.query.filter(
        Transaction.company_id == company_id,
        Transaction.categorization_status == 'uncategorized'
    ).limit(limit).all()

    high_confidence = 0
    medium_confidence = 0
    low_confidence = 0
    categorized = 0
    needs_review = 0
    auto_approved = 0

    for t in transactions:
        result = local_classify(
            t.description or '',
            t.vendor_name or '',
            float(t.amount) if t.amount else 0,
            company_id,
        )

        category = result['category']
        confidence = result['confidence']

        t.suggested_category = category
        t.suggested_confidence = confidence
        raw = t.raw_data or {}
        raw['ai_explanation'] = result.get('explanation', category)
        raw['classification_source'] = result.get('source', 'unknown')
        t.raw_data = raw

        # Try to link to a GAAP account record
        acct_number = result.get('account_number') or (category.split()[0] if category else None)
        if acct_number:
            acct_obj = gaap_accounts.get(acct_number)
            if acct_obj:
                t.account_id = acct_obj.id
                t.account_name = acct_obj.name

        if confidence >= 80:
            high_confidence += 1
        elif confidence >= 50:
            medium_confidence += 1
        else:
            low_confidence += 1

        if confidence >= 80 and auto_approve:
            t.category = category
            t.categorization_status = 'categorized'
            t.categorized_by = 'ai'
            t.review_status = 'approved'
            t.categorized_at = datetime.utcnow()
            auto_approved += 1
            categorized += 1
        else:
            t.categorization_status = 'suggested'
            t.review_status = 'pending'
            needs_review += 1

    db.session.commit()

    total = len(transactions)
    return jsonify({
        'success': True,
        'processed': total,
        'summary': {
            'total': total,
            'high_confidence': high_confidence,
            'medium_confidence': medium_confidence,
            'low_confidence': low_confidence,
            'categorized': categorized,
            'needs_review': needs_review,
        },
        'auto_approved': auto_approved
    })


@bp.route('/companies/<int:company_id>/setup-gaap-coa', methods=['POST'])
@login_required
def setup_gaap_coa(company_id):
    """Seed GAAP/AICPA standard chart of accounts for a company"""
    from app.services.gaap_coa import seed_gaap_accounts

    company = Company.query.filter_by(id=company_id, user_id=current_user.id).first()
    if not company:
        return jsonify({'success': False, 'error': 'Company not found'}), 404

    result = seed_gaap_accounts(company_id)
    return jsonify({
        'success': True,
        'message': f"GAAP chart of accounts ready: {result['created']} created, {result['skipped']} already existed",
        **result
    })


@bp.route('/companies/<int:company_id>/ai-metrics', methods=['GET'])
@login_required
def get_company_ai_metrics(company_id):
    """Get AI categorization metrics for a company"""
    company = Company.query.filter_by(id=company_id, user_id=current_user.id).first()
    if not company:
        return jsonify({'success': False, 'error': 'Company not found'}), 404

    days = request.args.get('days', 30, type=int)

    total = Transaction.query.filter_by(company_id=company_id).count()
    categorized = Transaction.query.filter(
        Transaction.company_id == company_id,
        Transaction.categorization_status == 'categorized'
    ).count()
    approved = Transaction.query.filter(
        Transaction.company_id == company_id,
        Transaction.review_status == 'approved'
    ).count()
    corrections = Transaction.query.filter(
        Transaction.company_id == company_id,
        Transaction.categorized_by == 'user',
        Transaction.review_status == 'approved'
    ).count()

    accuracy = (approved - corrections) / approved if approved > 0 else 0.0

    high = Transaction.query.filter(
        Transaction.company_id == company_id,
        Transaction.suggested_confidence >= 80
    ).count()
    medium = Transaction.query.filter(
        Transaction.company_id == company_id,
        Transaction.suggested_confidence >= 50,
        Transaction.suggested_confidence < 80
    ).count()
    low = Transaction.query.filter(
        Transaction.company_id == company_id,
        Transaction.suggested_confidence < 50
    ).count()

    return jsonify({
        'metrics': {
            'accuracy_rate': round(accuracy, 4),
            'total_transactions': total,
            'correct_categorizations': approved - corrections,
            'corrections_made': corrections,
        },
        'confidence_distribution': {
            'high': high,
            'medium': medium,
            'low': low,
        },
        'recent_corrections': [],
        'period_days': days
    })


@bp.route('/companies/<int:company_id>/sync', methods=['POST'])
@login_required
def sync_company(company_id):
    """Trigger sync for a specific company"""
    company = Company.query.filter_by(id=company_id, user_id=current_user.id).first()
    if not company:
        return jsonify({'success': False, 'error': 'Company not found'}), 404

    data = request.get_json() or {}
    sync_type = data.get('type', 'full')

    company.sync_status = 'syncing'
    db.session.commit()

    return jsonify({
        'success': True,
        'message': f'Sync ({sync_type}) initiated for {company.qbo_company_name or company.name}',
        'company_id': company_id
    })


# ============================================================================
# Billing JSON API (for React frontend - /api/v1/billing/*)
# ============================================================================

@bp.route('/billing/plans', methods=['GET'])
@login_required
def api_billing_plans():
    """Return subscription plans as JSON"""
    from app.models.subscription import SubscriptionPlan
    from app.routes.billing import _create_default_plans

    plans = SubscriptionPlan.query.filter_by(is_active=True).order_by(
        SubscriptionPlan.price_monthly
    ).all()
    if not plans:
        _create_default_plans()
        plans = SubscriptionPlan.query.filter_by(is_active=True).order_by(
            SubscriptionPlan.price_monthly
        ).all()

    return jsonify({
        'success': True,
        'plans': {p.name: p.to_dict() for p in plans}
    })


@bp.route('/billing/subscription', methods=['GET'])
@login_required
def api_billing_subscription():
    """Return current user subscription as JSON"""
    from app.models.subscription import UserSubscription

    subscription = UserSubscription.query.filter_by(user_id=current_user.id).first()
    if not subscription:
        return jsonify({
            'success': True,
            'subscription': None,
            'has_active_subscription': False
        })

    return jsonify({
        'success': True,
        'subscription': subscription.to_dict(),
        'has_active_subscription': subscription.is_active
    })


@bp.route('/transactions/<int:transaction_id>', methods=['GET'])
@login_required
def get_transaction(transaction_id):
    """Get a single transaction with full detail"""
    txn = Transaction.query.get_or_404(transaction_id)
    company = Company.query.filter_by(id=txn.company_id, user_id=current_user.id).first()
    if not company:
        return jsonify({'success': False, 'error': 'Access denied'}), 403
    return jsonify({'success': True, 'transaction': txn.to_dict()})


@bp.route('/transactions/<int:transaction_id>', methods=['PUT'])
@login_required
def update_transaction(transaction_id):
    """Update editable fields on a transaction"""
    txn = Transaction.query.get_or_404(transaction_id)
    company = Company.query.filter_by(id=txn.company_id, user_id=current_user.id).first()
    if not company:
        return jsonify({'success': False, 'error': 'Access denied'}), 403

    data = request.get_json() or {}

    if 'description' in data:
        txn.description = data['description'].strip() or txn.description
    if 'memo' in data:
        txn.memo = data['memo']
    if 'vendor_name' in data:
        txn.vendor_name = data['vendor_name']
    if 'customer_name' in data:
        txn.customer_name = data['customer_name']
    if 'transaction_date' in data and data['transaction_date']:
        try:
            txn.transaction_date = datetime.strptime(data['transaction_date'], '%Y-%m-%d').date()
        except ValueError:
            return jsonify({'success': False, 'error': 'Invalid date format, use YYYY-MM-DD'}), 422
    if 'amount' in data:
        try:
            txn.amount = float(data['amount'])
        except (ValueError, TypeError):
            return jsonify({'success': False, 'error': 'Invalid amount'}), 422

    # Category / account reclassification
    if 'category' in data and data['category']:
        txn.category = data['category']
        txn.categorization_status = 'categorized'
        txn.categorized_by = 'user'
        txn.categorized_at = datetime.utcnow()
        txn.review_status = 'approved'
        txn.reviewed_by_user_id = current_user.id
        txn.reviewed_at = datetime.utcnow()

    if 'account_id' in data and data['account_id']:
        acct = Account.query.get(data['account_id'])
        if acct and acct.company_id == company.id:
            txn.account_id = acct.id
            txn.account_name = acct.name
            txn.category = f"{acct.account_number} {acct.name}" if acct.account_number else acct.name
            txn.categorization_status = 'categorized'
            txn.categorized_by = 'user'
            txn.categorized_at = datetime.utcnow()
            txn.review_status = 'approved'
            txn.reviewed_by_user_id = current_user.id
            txn.reviewed_at = datetime.utcnow()

    db.session.commit()
    return jsonify({'success': True, 'transaction': txn.to_dict()})


@bp.route('/accounts', methods=['POST'])
@login_required
def create_account():
    """Create a new account in the Chart of Accounts"""
    data = request.get_json() or {}

    name = (data.get('name') or '').strip()
    account_type = (data.get('account_type') or '').strip()
    if not name or not account_type:
        return jsonify({'success': False, 'error': 'name and account_type are required'}), 422

    company = Company.query.filter_by(user_id=current_user.id).first()
    if not company:
        return jsonify({'success': False, 'error': 'No company found'}), 404

    import uuid
    acct = Account(
        company_id=company.id,
        qbo_account_id=f'manual-{uuid.uuid4().hex[:12]}',
        name=name,
        account_type=account_type,
        account_sub_type=data.get('account_sub_type') or account_type,
        classification=data.get('classification') or _infer_classification(account_type),
        account_number=data.get('account_number') or '',
        description=data.get('description') or '',
        is_active=True,
        current_balance=0,
    )
    db.session.add(acct)
    db.session.commit()
    return jsonify({'success': True, 'account': acct.to_dict()}), 201


@bp.route('/accounts/<int:account_id>', methods=['PUT'])
@login_required
def update_account(account_id):
    """Update an account"""
    acct = Account.query.get_or_404(account_id)
    company = Company.query.filter_by(id=acct.company_id, user_id=current_user.id).first()
    if not company:
        return jsonify({'success': False, 'error': 'Access denied'}), 403

    data = request.get_json() or {}
    if 'name' in data and data['name'].strip():
        acct.name = data['name'].strip()
    if 'account_type' in data:
        acct.account_type = data['account_type']
        acct.classification = _infer_classification(data['account_type'])
    if 'account_number' in data:
        acct.account_number = data['account_number']
    if 'description' in data:
        acct.description = data['description']
    if 'is_active' in data:
        acct.is_active = bool(data['is_active'])

    db.session.commit()
    return jsonify({'success': True, 'account': acct.to_dict()})


@bp.route('/accounts/<int:account_id>', methods=['DELETE'])
@login_required
def delete_account(account_id):
    """Deactivate (soft-delete) an account"""
    acct = Account.query.get_or_404(account_id)
    company = Company.query.filter_by(id=acct.company_id, user_id=current_user.id).first()
    if not company:
        return jsonify({'success': False, 'error': 'Access denied'}), 403

    acct.is_active = False
    db.session.commit()
    return jsonify({'success': True, 'message': f'Account "{acct.name}" deactivated'})


def _infer_classification(account_type: str) -> str:
    t = account_type.lower()
    if any(x in t for x in ('asset', 'bank', 'receivable', 'inventory', 'fixed')):
        return 'Asset'
    if any(x in t for x in ('liability', 'payable', 'credit card', 'loan', 'debt')):
        return 'Liability'
    if any(x in t for x in ('equity', 'retained', 'capital', 'draw')):
        return 'Equity'
    if any(x in t for x in ('income', 'revenue', 'sales')):
        return 'Revenue'
    return 'Expense'


@bp.route('/billing/create-checkout', methods=['POST'])
@login_required
def api_billing_create_checkout():
    """Create a checkout session (Stripe scaffold)"""
    from datetime import timedelta
    from app.models.subscription import SubscriptionPlan, UserSubscription
    from app.routes.billing import _create_default_plans, _create_trial_subscription

    data = request.get_json() or {}
    plan_type = data.get('plan_type', 'starter')

    plan = SubscriptionPlan.query.filter_by(name=plan_type, is_active=True).first()
    if not plan:
        _create_default_plans()
        plan = SubscriptionPlan.query.filter_by(name=plan_type).first()
    if not plan:
        return jsonify({'success': False, 'error': 'Plan not found'}), 404

    subscription = UserSubscription.query.filter_by(user_id=current_user.id).first()
    if subscription:
        subscription.plan_id = plan.id
        subscription.status = 'active'
        subscription.current_period_start = datetime.utcnow()
        subscription.current_period_end = datetime.utcnow() + timedelta(days=30)
    else:
        subscription = UserSubscription(
            user_id=current_user.id,
            plan_id=plan.id,
            billing_cycle='monthly',
            status='active',
            current_period_start=datetime.utcnow(),
            current_period_end=datetime.utcnow() + timedelta(days=30)
        )
        db.session.add(subscription)

    db.session.commit()

    return jsonify({
        'success': True,
        'checkout_url': f'/billing?plan={plan_type}&activated=1',
        'session_id': f'sess_{current_user.id}_{plan.id}'
    })


@bp.route('/nlq', methods=['POST'])
@login_required
def natural_language_query():
    """Parse a natural language query and return matching transactions."""
    from app.services.nlq_service import parse_nl_query
    data = request.get_json() or {}
    query_text = (data.get('query') or '').strip()
    if not query_text:
        return jsonify({'success': False, 'error': 'Query is required'}), 422

    company = Company.query.filter_by(user_id=current_user.id).first()
    if not company:
        return jsonify({'success': False, 'error': 'No company found'}), 404

    filters = parse_nl_query(query_text)

    q = Transaction.query.filter_by(company_id=company.id)
    if filters.get('date_from'):
        q = q.filter(Transaction.transaction_date >= filters['date_from'])
    if filters.get('date_to'):
        q = q.filter(Transaction.transaction_date <= filters['date_to'])
    if filters.get('min_amount') is not None:
        q = q.filter(db.func.abs(Transaction.amount) >= filters['min_amount'])
    if filters.get('max_amount') is not None:
        q = q.filter(db.func.abs(Transaction.amount) <= filters['max_amount'])
    if filters.get('vendor'):
        q = q.filter(Transaction.vendor_name.ilike(f"%{filters['vendor']}%"))
    if filters.get('category'):
        q = q.filter(db.or_(
            Transaction.category.ilike(f"%{filters['category']}%"),
            Transaction.suggested_category.ilike(f"%{filters['category']}%"),
        ))
    if filters.get('transaction_type') == 'expense':
        q = q.filter(Transaction.amount < 0)
    elif filters.get('transaction_type') == 'income':
        q = q.filter(Transaction.amount > 0)
    if filters.get('search'):
        s = f"%{filters['search']}%"
        q = q.filter(db.or_(
            Transaction.description.ilike(s),
            Transaction.vendor_name.ilike(s),
        ))

    total = q.count()
    rows = q.order_by(Transaction.transaction_date.desc()).limit(100).all()
    total_amount = sum(float(t.amount or 0) for t in rows)

    return jsonify({
        'success': True,
        'query': query_text,
        'filters': filters,
        'transactions': [t.to_dict() for t in rows],
        'total': total,
        'total_amount': round(total_amount, 2),
    })


@bp.route('/companies/<int:company_id>/settings', methods=['PUT'])
@login_required
def update_company_settings(company_id):
    """Update company fiscal year and timezone settings"""
    company = Company.query.filter_by(id=company_id, user_id=current_user.id).first()
    if not company:
        return jsonify({'success': False, 'error': 'Company not found'}), 404
    data = request.get_json() or {}
    if 'fiscal_year_start' in data:
        fys = int(data['fiscal_year_start'])
        if 1 <= fys <= 12:
            company.fiscal_year_start = fys
    if 'timezone' in data:
        company.timezone = data['timezone']
    db.session.commit()
    return jsonify({'success': True})
