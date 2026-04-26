"""Charts and Reports Routes"""
from flask import Blueprint, render_template, jsonify, request, send_file
from flask_login import login_required, current_user
from app.models import Transaction, Account, Company
from app import db
from datetime import datetime, timedelta
import json

bp = Blueprint('charts', __name__)


@bp.route('/api/v1/data/pnl')
@login_required
def pnl_data():
    """Get P&L data for charts"""
    # Get user's company
    company = Company.query.filter_by(user_id=current_user.id).first()
    if not company:
        return jsonify({'labels': [], 'income': [], 'expenses': [], 'profit': []})
    
    # Get date range (default: last 6 months)
    end_date = datetime.now()
    start_date = end_date - timedelta(days=180)
    
    # Query transactions by company
    transactions = Transaction.query.filter(
        Transaction.company_id == company.id,
        Transaction.transaction_date >= start_date.date(),
        Transaction.transaction_date <= end_date.date()
    ).all()
    
    # Calculate monthly data
    months = {}
    for t in transactions:
        month_key = t.transaction_date.strftime('%Y-%m')
        if month_key not in months:
            months[month_key] = {'income': 0, 'expenses': 0}
        
        amount = float(t.amount) if t.amount else 0
        if amount > 0:
            months[month_key]['income'] += amount
        else:
            months[month_key]['expenses'] += abs(amount)
    
    # Format for charts
    labels = sorted(months.keys())
    income_data = [months[m]['income'] for m in labels]
    expense_data = [months[m]['expenses'] for m in labels]
    profit_data = [income_data[i] - expense_data[i] for i in range(len(labels))]
    
    return jsonify({
        'labels': labels,
        'income': income_data,
        'expenses': expense_data,
        'profit': profit_data
    })


@bp.route('/api/v1/data/balance')
@login_required
def balance_data():
    """Get balance data for charts"""
    # Get user's company
    company = Company.query.filter_by(user_id=current_user.id).first()
    if not company:
        return jsonify({'assets': 0, 'liabilities': 0, 'equity': 0})
    
    # Get current balance by account type
    accounts = Account.query.filter_by(company_id=company.id).all()
    
    data = {
        'assets': 0,
        'liabilities': 0,
        'equity': 0
    }
    
    for account in accounts:
        balance = float(account.balance) if account.balance else 0
        if account.type == 'asset':
            data['assets'] += balance
        elif account.type == 'liability':
            data['liabilities'] += abs(balance)
        elif account.type == 'equity':
            data['equity'] += balance
    
    return jsonify(data)


@bp.route('/api/v1/data/expenses')
@login_required
def expenses_data():
    """Get expense breakdown by category"""
    # Get user's company
    company = Company.query.filter_by(user_id=current_user.id).first()
    if not company:
        return jsonify({'labels': [], 'data': []})
    
    transactions = Transaction.query.filter(
        Transaction.company_id == company.id,
        Transaction.amount < 0
    ).all()
    
    categories = {}
    for t in transactions:
        cat = t.category or 'Uncategorized'
        if cat not in categories:
            categories[cat] = 0
        amount = float(t.amount) if t.amount else 0
        categories[cat] += abs(amount)
    
    return jsonify({
        'labels': list(categories.keys()),
        'data': list(categories.values())
    })
