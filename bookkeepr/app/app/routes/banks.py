"""
Bank Routes for Plaid Integration
"""
from flask import Blueprint, jsonify, request
from flask_login import login_required, current_user
from extensions import db
from app.services.plaid_service import plaid_service
from app.models.bank_connection import BankConnection, BankAccount, BankTransaction
from app.services.ai_categorization import get_ai_categorization_service

bp = Blueprint('banks', __name__, url_prefix='/api/v1/banks')


@bp.route('/connect', methods=['POST'])
@login_required
def connect_bank():
    """Initialize Plaid Link"""
    result = plaid_service.create_link_token(current_user.id)
    
    if result['success']:
        return jsonify({
            'success': True,
            'link_token': result['link_token'],
            'expiration': result['expiration']
        })
    else:
        return jsonify({
            'success': False,
            'error': result.get('error', 'Failed to create link token')
        }), 400


@bp.route('/exchange', methods=['POST'])
@login_required
def exchange_token():
    """Exchange public token for access token"""
    data = request.get_json()
    public_token = data.get('public_token')
    institution_name = data.get('institution_name', 'Unknown Bank')
    
    if not public_token:
        return jsonify({'success': False, 'error': 'Public token required'}), 400
    
    # Exchange token
    result = plaid_service.exchange_public_token(public_token)
    
    if not result['success']:
        return jsonify(result), 400
    
    # Save connection
    connection = BankConnection(
        user_id=current_user.id,
        plaid_access_token=result['access_token'],
        plaid_item_id=result['item_id'],
        institution_name=institution_name,
        status='active'
    )
    db.session.add(connection)
    db.session.commit()
    
    # Get accounts
    accounts_result = plaid_service.get_accounts(result['access_token'])
    if accounts_result['success']:
        for account in accounts_result['accounts']:
            bank_account = BankAccount(
                connection_id=connection.id,
                plaid_account_id=account['account_id'],
                name=account['name'],
                official_name=account.get('official_name'),
                account_type=account['type'],
                account_subtype=account.get('subtype'),
                mask=account.get('mask')
            )
            db.session.add(bank_account)
        db.session.commit()
    
    return jsonify({
        'success': True,
        'connection_id': connection.id,
        'institution': institution_name
    })


@bp.route('/', methods=['GET'])
@login_required
def get_banks():
    """List connected banks"""
    connections = BankConnection.query.filter_by(
        user_id=current_user.id,
        status='active'
    ).all()
    
    return jsonify({
        'success': True,
        'banks': [conn.to_dict() for conn in connections]
    })


@bp.route('/<int:connection_id>', methods=['DELETE'])
@login_required
def disconnect_bank(connection_id):
    """Disconnect a bank"""
    connection = BankConnection.query.filter_by(
        id=connection_id,
        user_id=current_user.id
    ).first()
    
    if not connection:
        return jsonify({'success': False, 'error': 'Bank not found'}), 404
    
    connection.status = 'disconnected'
    db.session.commit()
    
    return jsonify({'success': True, 'message': 'Bank disconnected'})


@bp.route('/sync/<int:connection_id>', methods=['POST'])
@login_required
def sync_bank(connection_id):
    """Manually sync bank transactions"""
    connection = BankConnection.query.filter_by(
        id=connection_id,
        user_id=current_user.id
    ).first()
    
    if not connection:
        return jsonify({'success': False, 'error': 'Bank not found'}), 404
    
    # Get transactions
    result = plaid_service.get_transactions(connection.plaid_access_token)
    
    if not result['success']:
        return jsonify(result), 400
    
    # Save transactions
    imported_count = 0
    for transaction in result['transactions']:
        # Check for duplicates
        existing = BankTransaction.query.filter_by(
            plaid_transaction_id=transaction['transaction_id']
        ).first()
        
        if existing:
            continue
        
        # Create transaction
        bank_transaction = BankTransaction(
            account_id=transaction['account_id'],
            plaid_transaction_id=transaction['transaction_id'],
            amount=abs(transaction['amount']),
            is_debit=transaction['amount'] > 0,
            date=transaction['date'],
            description=transaction['name'],
            merchant_name=transaction.get('merchant_name'),
            category=transaction.get('category', [None])[0],
            pending=transaction.get('pending', False)
        )
        
        # AI categorization
        service = get_categorization_service()
        category, confidence = service.categorize(bank_transaction.description)
        bank_transaction.ai_category = category
        bank_transaction.ai_confidence = confidence
        
        db.session.add(bank_transaction)
        imported_count += 1
    
    db.session.commit()
    
    return jsonify({
        'success': True,
        'imported': imported_count,
        'total_available': result['total_transactions']
    })


@bp.route('/transactions', methods=['GET'])
@login_required
def get_transactions():
    """Get all bank transactions"""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 50, type=int)
    
    transactions = BankTransaction.query.join(
        BankAccount, BankAccount.plaid_account_id == BankTransaction.account_id
    ).join(
        BankConnection, BankConnection.id == BankAccount.connection_id
    ).filter(
        BankConnection.user_id == current_user.id
    ).order_by(
        BankTransaction.date.desc()
    ).paginate(page=page, per_page=per_page)
    
    return jsonify({
        'success': True,
        'transactions': [t.to_dict() for t in transactions.items],
        'total': transactions.total,
        'pages': transactions.pages,
        'current_page': page
    })
