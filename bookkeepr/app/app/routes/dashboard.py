"""Dashboard Routes"""
from flask import Blueprint, render_template, flash, current_app
from flask_login import login_required, current_user

bp = Blueprint('dashboard', __name__)


@bp.route('/')
@login_required
def index():
    """Main dashboard"""
    return render_template('dashboard/index.html')


@bp.route('/transactions')
@login_required
def transactions():
    """Transaction list"""
    return render_template('dashboard/transactions.html')


@bp.route('/transactions/<int:transaction_id>')
@login_required
def transaction_detail(transaction_id):
    """Transaction detail view"""
    return render_template('dashboard/transaction_detail.html', transaction_id=transaction_id)


@bp.route('/accounts')
@login_required
def accounts():
    """Chart of accounts"""
    return render_template('dashboard/accounts.html')


@bp.route('/settings')
@login_required
def settings():
    """User settings"""
    return render_template('dashboard/settings.html')


@bp.route('/settings/company')
@login_required
def company_settings():
    """Company/QBO connection settings"""
    return render_template('dashboard/company_settings.html')
