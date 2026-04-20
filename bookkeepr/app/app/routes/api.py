"""API Routes"""
from flask import Blueprint, jsonify, request
from flask_login import login_required, current_user

bp = Blueprint('api', __name__)


@bp.route('/health')
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'service': 'BookKeepr AI'
    })


@bp.route('/user', methods=['GET'])
@login_required
def get_user():
    """Get current user info"""
    return jsonify(current_user.to_dict())


@bp.route('/transactions', methods=['GET'])
@login_required
def list_transactions():
    """List transactions"""
    return jsonify({
        'transactions': [],
        'total': 0,
        'page': 1,
        'per_page': 20
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
