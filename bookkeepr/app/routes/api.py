"""
API Routes - REST API for BookKeepr
"""
from flask import Blueprint, jsonify, request, session
from flask_login import login_required, current_user
from app import db
from app.models.company import Company
from app.models.transaction import Transaction
from app.models.account import Account
from app.models.category_rule import CategoryRule
from app.services.qb_service import QuickBooksService
from app.services.ai_categorization import (
    get_ai_categorization_service,
    get_learning_system
)
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)
api_bp = Blueprint('api', __name__, url_prefix='/api/v1')


@api_bp.route('/login', methods=['POST'])
def api_login():
    """
    Email/password login for API (for testing without OAuth)
    """
    from app.models.user import User
    from flask_login import login_user
    
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')
    
    if not email or not password:
        return jsonify({'error': 'Email and password required'}), 400
    
    user = User.query.filter_by(email=email).first()
    
    if user and user.check_password(password):
        login_user(user, remember=True)
        return jsonify({
            'success': True,
            'user': {
                'id': user.id,
                'email': user.email,
                'first_name': user.first_name,
                'last_name': user.last_name
            }
        })
    
    return jsonify({'error': 'Invalid credentials'}), 401


@api_bp.route('/logout', methods=['POST'])
@login_required
def api_logout():
    """Logout current user"""
    from flask_login import logout_user
    logout_user()
    return jsonify({'success': True})


@api_bp.route('/me', methods=['GET'])
@login_required
def get_current_user():
    """Get current logged in user"""
    return jsonify({
        'id': current_user.id,
        'email': current_user.email,
        'first_name': current_user.first_name,
        'last_name': current_user.last_name
    })


@api_bp.route('/companies', methods=['GET'])
@login_required
def get_companies():
    """Get user's companies"""
    companies = current_user.companies.all()
    return jsonify([c.to_dict() for c in companies])


@api_bp.route('/companies/<int:company_id>/sync/accounts', methods=['POST'])
@login_required
def sync_company_accounts(company_id):
    """Sync chart of accounts only"""
    company = Company.query.get_or_404(company_id)
    
    if company.user_id != current_user.id:
        return jsonify({'error': 'Unauthorized'}), 403
    
    try:
        qb_service = QuickBooksService(company)
        result = qb_service.sync_accounts()
        
        return jsonify({
            'success': True,
            'type': 'accounts',
            'created': result.get('created', 0),
            'updated': result.get('updated', 0),
            'errors': result.get('errors', 0),
            'total': result.get('created', 0) + result.get('updated', 0),
            'message': f"Synced {result.get('created', 0)} new accounts, updated {result.get('updated', 0)}"
        })
    except Exception as e:
        logger.error(f"Account sync failed: {e}")
        return jsonify({'error': 'Account sync failed', 'message': str(e)}), 500


@api_bp.route('/companies/<int:company_id>/sync', methods=['POST'])
@login_required
def sync_company(company_id):
    """Trigger manual sync for company"""
    company = Company.query.get_or_404(company_id)
    
    if company.user_id != current_user.id:
        return jsonify({'error': 'Unauthorized'}), 403
    
    # Parse request params
    data = request.get_json() or {}
    sync_type = data.get('type', 'full')  # 'full', 'accounts', 'transactions'
    
    # Date range (optional)
    start_date = None
    end_date = None
    if 'start_date' in data:
        start_date = datetime.fromisoformat(data['start_date'])
    if 'end_date' in data:
        end_date = datetime.fromisoformat(data['end_date'])
    
    try:
        qb_service = QuickBooksService(company)
        
        if sync_type == 'accounts':
            result = qb_service.sync_accounts()
            return jsonify({
                'success': True,
                'type': 'accounts',
                'synced': result.get('created', 0) + result.get('updated', 0),
                'created': result.get('created', 0),
                'updated': result.get('updated', 0),
                'errors': result.get('errors', 0),
                'message': f"Synced {result.get('created', 0)} new accounts, updated {result.get('updated', 0)}"
            })
        
        elif sync_type == 'transactions':
            result = qb_service.sync_transactions(start_date=start_date, end_date=end_date)
            return jsonify({
                'success': True,
                'type': 'transactions',
                'synced': result.get('count', 0) + result.get('updated', 0),
                'created': result.get('count', 0),
                'updated': result.get('updated', 0),
                'skipped': result.get('skipped', 0),
                'errors': result.get('errors', 0),
                'message': f"Synced {result.get('count', 0)} new transactions, updated {result.get('updated', 0)}"
            })
        
        else:  # full sync
            result = qb_service.sync_all(start_date=start_date, end_date=end_date)
            return jsonify({
                'success': result.get('success', True),
                'type': 'full',
                'accounts': result.get('accounts', {}),
                'transactions': result.get('transactions', {}),
                'message': f"Full sync complete"
            })
            
    except Exception as e:
        logger.error(f"Sync failed: {e}")
        return jsonify({'error': 'Sync failed', 'message': str(e)}), 500


@api_bp.route('/sync-session', methods=['POST'])
def sync_session():
    """Sync using session tokens (no company DB record needed)"""
    tokens = session.get('qb_tokens', {})
    if not tokens.get('access_token'):
        return jsonify({'error': 'Not authenticated'}), 401
    
    # Parse request params
    data = request.get_json() or {}
    sync_type = data.get('type', 'transactions')
    
    # Date range (optional)
    start_date = None
    end_date = None
    if 'start_date' in data:
        start_date = datetime.fromisoformat(data['start_date'])
    if 'end_date' in data:
        end_date = datetime.fromisoformat(data['end_date'])
    
    try:
        # Create a mock company object with session data and required methods
        class MockCompany:
            def __init__(self, tokens):
                self.realm_id = tokens.get('realm_id')
                self.access_token = tokens.get('access_token')
                self.refresh_token = tokens.get('refresh_token')
                self.token_expires_at = datetime.utcnow() + timedelta(hours=1)
                self.last_sync_at = None
                self.id = 'session'
            
            def needs_token_refresh(self):
                """Check if token needs refresh (simplified for session)"""
                return False
            
            def update_sync_status(self, status, error=None):
                """No-op for session sync"""
                pass
        
        company = MockCompany(tokens)
        
        qb_service = QuickBooksService(company)
        
        if sync_type == 'accounts':
            result = qb_service.sync_accounts()
            return jsonify({
                'success': True,
                'type': 'accounts',
                'synced': result.get('created', 0) + result.get('updated', 0),
                'message': f"Synced {result.get('created', 0)} accounts, updated {result.get('updated', 0)}"
            })
        else:
            result = qb_service.sync_transactions(start_date=start_date, end_date=end_date)
            return jsonify({
                'success': True,
                'type': 'transactions',
                'synced': result.get('count', 0) + result.get('updated', 0),
                'created': result.get('count', 0),
                'updated': result.get('updated', 0),
                'skipped': result.get('skipped', 0),
                'message': f"Synced {result.get('count', 0)} transactions, updated {result.get('updated', 0)}"
            })
            
    except Exception as e:
        logger.error(f"Sync failed: {e}")
        return jsonify({'error': 'Sync failed', 'message': str(e)}), 500


@api_bp.route('/companies/<int:company_id>/transactions', methods=['GET'])
@login_required
def get_transactions(company_id):
    """Get transactions for company"""
    company = Company.query.get_or_404(company_id)
    
    if company.user_id != current_user.id:
        return jsonify({'error': 'Unauthorized'}), 403
    
    # Query params
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 25, type=int)
    needs_review = request.args.get('needs_review', type=bool)
    
    query = Transaction.query.filter_by(company_id=company_id)
    
    if needs_review is not None:
        query = query.filter_by(needs_review=needs_review)
    
    transactions = query.order_by(Transaction.transaction_date.desc())\
        .paginate(page=page, per_page=per_page)
    
    return jsonify({
        'transactions': [t.to_dict() for t in transactions.items],
        'total': transactions.total,
        'pages': transactions.pages,
        'current_page': page
    })


@api_bp.route('/transactions/<int:transaction_id>/categorize', methods=['POST'])
@login_required
def categorize_transaction(transaction_id):
    """Categorize a transaction"""
    transaction = Transaction.query.get_or_404(transaction_id)
    company = Company.query.get(transaction.company_id)
    
    if company.user_id != current_user.id:
        return jsonify({'error': 'Unauthorized'}), 403
    
    data = request.get_json()
    account_id = data.get('account_id')
    
    if not account_id:
        return jsonify({'error': 'account_id required'}), 400
    
    transaction.categorize(account_id, confidence=1.0, user_id=current_user.id)
    transaction.approve(current_user.id)
    
    db.session.commit()
    
    return jsonify({
        'success': True,
        'transaction': transaction.to_dict()
    })


@api_bp.route('/companies/<int:company_id>/accounts', methods=['GET'])
@login_required
def get_accounts(company_id):
    """Get chart of accounts"""
    company = Company.query.get_or_404(company_id)
    
    if company.user_id != current_user.id:
        return jsonify({'error': 'Unauthorized'}), 403
    
    account_type = request.args.get('type')
    
    if account_type:
        accounts = Account.get_by_type(company_id, account_type)
    else:
        accounts = company.get_chart_of_accounts()
    
    return jsonify([a.to_dict() for a in accounts])


@api_bp.route('/companies/<int:company_id>/rules', methods=['GET', 'POST'])
@login_required
def manage_rules(company_id):
    """Get or create category rules"""
    company = Company.query.get_or_404(company_id)
    
    if company.user_id != current_user.id:
        return jsonify({'error': 'Unauthorized'}), 403
    
    if request.method == 'GET':
        rules = CategoryRule.get_active_rules(current_user.id, company_id)
        return jsonify([r.to_dict() for r in rules])
    
    elif request.method == 'POST':
        data = request.get_json()
        
        rule = CategoryRule(
            user_id=current_user.id,
            company_id=company_id,
            name=data.get('name'),
            rule_type=data.get('rule_type', 'keyword'),
            keyword=data.get('keyword'),
            vendor_name=data.get('vendor_name'),
            min_amount=data.get('min_amount'),
            max_amount=data.get('max_amount'),
            target_account_id=data.get('target_account_id'),
            priority=data.get('priority', 100)
        )
        
        db.session.add(rule)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'rule': rule.to_dict()
        }), 201


# ============================================================================
# AI Categorization Routes (Phase 2)
# ============================================================================

@api_bp.route('/companies/<int:company_id>/ai-categorize', methods=['POST'])
@login_required
def ai_categorize_company(company_id):
    """
    Run AI categorization on uncategorized transactions
    
    POST body:
        - limit: Max transactions to process (default: 100)
        - auto_approve_high_confidence: Auto-approve high confidence results
        - transaction_ids: Optional list of specific transaction IDs to categorize
    """
    company = Company.query.get_or_404(company_id)
    
    if company.user_id != current_user.id:
        return jsonify({'error': 'Unauthorized'}), 403
    
    data = request.get_json() or {}
    limit = data.get('limit', 100)
    auto_approve = data.get('auto_approve_high_confidence', True)
    transaction_ids = data.get('transaction_ids')
    
    try:
        from app.services.ai_categorization import get_ai_categorization_service
        
        # Get transactions to categorize
        if transaction_ids:
            transactions = Transaction.query.filter(
                Transaction.id.in_(transaction_ids),
                Transaction.company_id == company_id
            ).all()
        else:
            transactions = Transaction.get_uncategorized(company_id, limit=limit)
        
        if not transactions:
            return jsonify({
                'success': True,
                'message': 'No uncategorized transactions found',
                'processed': 0,
                'results': {}
            })
        
        # Run AI categorization
        ai_service = get_ai_categorization_service()
        results = ai_service.categorize_batch(transactions, company_id)
        
        # Summarize results
        summary = {
            'total': len(results),
            'high_confidence': sum(1 for r in results if r.confidence_level.value == 'high'),
            'medium_confidence': sum(1 for r in results if r.confidence_level.value == 'medium'),
            'low_confidence': sum(1 for r in results if r.confidence_level.value == 'low'),
            'categorized': sum(1 for r in results if r.account_id is not None),
            'needs_review': sum(1 for r in results if r.confidence_level.value in ['low', 'medium'])
        }
        
        # Auto-approve high confidence if requested
        approved_count = 0
        if auto_approve:
            for result in results:
                if result.confidence_level.value == 'high' and result.account_id:
                    tx = Transaction.query.get(result.transaction_id)
                    if tx:
                        tx.approve(current_user.id)
                        approved_count += 1
            
            db.session.commit()
        
        return jsonify({
            'success': True,
            'processed': len(results),
            'summary': summary,
            'auto_approved': approved_count,
            'results': [
                {
                    'transaction_id': r.transaction_id,
                    'account_id': r.account_id,
                    'account_name': r.account_name,
                    'confidence': r.confidence,
                    'confidence_level': r.confidence_level.value,
                    'reason': r.reason,
                    'suggestions': r.suggestions
                }
                for r in results
            ]
        })
        
    except Exception as e:
        logger.error(f"AI categorization failed: {e}")
        return jsonify({'error': 'Categorization failed', 'message': str(e)}), 500


@api_bp.route('/companies/<int:company_id>/review-queue', methods=['GET'])
@login_required
def get_review_queue(company_id):
    """
    Get transactions that need manual review
    
    Query params:
        - status: Filter by status (pending, categorized, approved)
        - confidence: Filter by confidence (low, medium, high)
        - limit: Max results (default: 50)
        - page: Page number for pagination
    """
    company = Company.query.get_or_404(company_id)
    
    if company.user_id != current_user.id:
        return jsonify({'error': 'Unauthorized'}), 403
    
    status = request.args.get('status', 'pending')
    confidence = request.args.get('confidence')
    limit = request.args.get('limit', 50, type=int)
    page = request.args.get('page', 1, type=int)
    
    query = Transaction.query.filter_by(
        company_id=company_id,
        needs_review=True
    )
    
    if status:
        query = query.filter_by(status=status)
    
    if confidence == 'low':
        query = query.filter(Transaction.category_confidence < 0.70)
    elif confidence == 'medium':
        query = query.filter(
            Transaction.category_confidence >= 0.70,
            Transaction.category_confidence < 0.85
        )
    elif confidence == 'high':
        query = query.filter(Transaction.category_confidence >= 0.85)
    
    transactions = query.order_by(Transaction.transaction_date.desc())\
        .paginate(page=page, per_page=limit)
    
    # Get account names for suggestions
    result = []
    for tx in transactions.items:
        tx_dict = tx.to_dict()
        tx_dict['suggestions'] = tx.category_suggestions or []
        
        # Get account names for suggestions
        for sug in tx_dict['suggestions']:
            account = Account.query.get(sug.get('account_id'))
            if account:
                sug['account_name'] = account.name
        
        result.append(tx_dict)
    
    return jsonify({
        'transactions': result,
        'total': transactions.total,
        'pages': transactions.pages,
        'current_page': page
    })


@api_bp.route('/transactions/<int:transaction_id>/review', methods=['POST'])
@login_required
def review_transaction(transaction_id):
    """
    Review and approve/reject/correct an AI categorization
    
    POST body:
        - action: 'approve', 'reject', or 'correct'
        - account_id: Required for 'correct' action
        - notes: Optional review notes
    """
    transaction = Transaction.query.get_or_404(transaction_id)
    company = Company.query.get(transaction.company_id)
    
    if company.user_id != current_user.id:
        return jsonify({'error': 'Unauthorized'}), 403
    
    data = request.get_json()
    action = data.get('action')
    
    if action not in ['approve', 'reject', 'correct']:
        return jsonify({'error': 'Invalid action. Use: approve, reject, or correct'}), 400
    
    try:
        if action == 'approve':
            transaction.approve(current_user.id)
            message = 'Transaction approved'
            
        elif action == 'reject':
            transaction.needs_review = True
            transaction.review_reason = data.get('notes', 'Rejected by user')
            transaction.status = 'rejected'
            message = 'Transaction rejected'
            
        elif action == 'correct':
            account_id = data.get('account_id')
            if not account_id:
                return jsonify({'error': 'account_id required for correction'}), 400
            
            # Record correction for learning
            original_account_id = transaction.category_id
            
            transaction.categorize(account_id, confidence=1.0, user_id=current_user.id)
            transaction.approve(current_user.id)
            
            # Log correction for learning system
            from app.services.ai_categorization import get_learning_system
            learning_system = get_learning_system()
            learning_system.record_correction(
                transaction=transaction,
                original_account_id=original_account_id,
                corrected_account_id=account_id,
                user_id=current_user.id
            )
            
            message = 'Transaction corrected and approved'
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': message,
            'transaction': transaction.to_dict()
        })
        
    except Exception as e:
        logger.error(f"Review failed: {e}")
        return jsonify({'error': 'Review failed', 'message': str(e)}), 500


@api_bp.route('/transactions/bulk-review', methods=['POST'])
@login_required
def bulk_review_transactions():
    """
    Bulk approve or correct transactions
    
    POST body:
        - transaction_ids: List of transaction IDs
        - action: 'approve' or 'correct'
        - account_id: Required for 'correct' action
    """
    data = request.get_json()
    transaction_ids = data.get('transaction_ids', [])
    action = data.get('action')
    
    if not transaction_ids:
        return jsonify({'error': 'transaction_ids required'}), 400
    
    if action not in ['approve', 'correct']:
        return jsonify({'error': 'Invalid action. Use: approve or correct'}), 400
    
    if action == 'correct' and not data.get('account_id'):
        return jsonify({'error': 'account_id required for correct action'}), 400
    
    try:
        transactions = Transaction.query.filter(
            Transaction.id.in_(transaction_ids)
        ).all()
        
        processed = 0
        errors = []
        
        for tx in transactions:
            company = Company.query.get(tx.company_id)
            if company.user_id != current_user.id:
                errors.append(f'Unauthorized for transaction {tx.id}')
                continue
            
            if action == 'approve':
                tx.approve(current_user.id)
                processed += 1
                
            elif action == 'correct':
                original_account_id = tx.category_id
                tx.categorize(data['account_id'], confidence=1.0, user_id=current_user.id)
                tx.approve(current_user.id)
                
                # Log correction
                from app.services.ai_categorization import get_learning_system
                learning_system = get_learning_system()
                learning_system.record_correction(
                    transaction=tx,
                    original_account_id=original_account_id,
                    corrected_account_id=data['account_id'],
                    user_id=current_user.id
                )
                processed += 1
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'processed': processed,
            'errors': errors,
            'message': f'Processed {processed} transactions'
        })
        
    except Exception as e:
        logger.error(f"Bulk review failed: {e}")
        return jsonify({'error': 'Bulk review failed', 'message': str(e)}), 500


@api_bp.route('/companies/<int:company_id>/ai-metrics', methods=['GET'])
@login_required
def get_ai_metrics(company_id):
    """
    Get AI categorization accuracy metrics
    
    Query params:
        - days: Number of days to analyze (default: 30)
    """
    company = Company.query.get_or_404(company_id)
    
    if company.user_id != current_user.id:
        return jsonify({'error': 'Unauthorized'}), 403
    
    days = request.args.get('days', 30, type=int)
    
    try:
        from app.services.ai_categorization import get_learning_system
        
        learning_system = get_learning_system()
        metrics = learning_system.get_accuracy_metrics(company_id, days=days)
        
        # Additional stats
        from app.models.correction_log import CorrectionLog
        
        recent_corrections = CorrectionLog.get_recent(company_id, limit=10)
        
        # Confidence distribution
        confidence_dist = db.session.query(
            db.func.case(
                (Transaction.category_confidence >= 0.85, 'high'),
                (Transaction.category_confidence >= 0.70, 'medium'),
                else_='low'
            ).label('level'),
            db.func.count(Transaction.id)
        ).filter(
            Transaction.company_id == company_id,
            Transaction.ai_processed == True
        ).group_by('level').all()
        
        return jsonify({
            'metrics': metrics,
            'confidence_distribution': {level: count for level, count in confidence_dist},
            'recent_corrections': [c.to_dict() for c in recent_corrections],
            'period_days': days
        })
        
    except Exception as e:
        logger.error(f"Metrics calculation failed: {e}")
        return jsonify({'error': 'Failed to calculate metrics', 'message': str(e)}), 500


@api_bp.route('/companies/<int:company_id>/learned-rules', methods=['GET'])
@login_required
def get_learned_rules(company_id):
    """Get AI-learned category rules"""
    company = Company.query.get_or_404(company_id)
    
    if company.user_id != current_user.id:
        return jsonify({'error': 'Unauthorized'}), 403
    
    rules = CategoryRule.query.filter_by(
        user_id=current_user.id,
        company_id=company_id,
        is_ai_learned=True
    ).order_by(CategoryRule.match_count.desc()).all()
    
    return jsonify([r.to_dict() for r in rules])
