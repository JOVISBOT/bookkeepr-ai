"""
Bank Routes - Plaid integration (not yet configured)
"""
from flask import Blueprint, jsonify
from flask_login import login_required

bp = Blueprint('banks', __name__, url_prefix='/api/v1/banks')


def _not_configured():
    return jsonify({'success': False, 'error': 'Bank integration not configured'}), 501


@bp.route('/connect', methods=['POST'])
@login_required
def connect_bank():
    return _not_configured()


@bp.route('/exchange', methods=['POST'])
@login_required
def exchange_token():
    return _not_configured()


@bp.route('/', methods=['GET'])
@login_required
def get_banks():
    return jsonify({'success': True, 'banks': []})


@bp.route('/<int:connection_id>', methods=['DELETE'])
@login_required
def disconnect_bank(connection_id):
    return _not_configured()


@bp.route('/sync/<int:connection_id>', methods=['POST'])
@login_required
def sync_bank(connection_id):
    return _not_configured()


@bp.route('/transactions', methods=['GET'])
@login_required
def get_transactions():
    return jsonify({'success': True, 'transactions': [], 'total': 0, 'pages': 0, 'current_page': 1})
