"""Client Portal — what your clients see when they log in"""
from datetime import datetime, timedelta
from flask import Blueprint, render_template, jsonify, request, redirect, url_for, flash
from flask_login import login_required, current_user

from extensions import db
from app.models.transaction import Transaction
from app.models.company import Company
from app.models.account import Account

bp = Blueprint('portal', __name__, url_prefix='/portal')


def require_client(f):
    """Restrict to client-role or viewer-role users only"""
    from functools import wraps
    @wraps(f)
    def decorated(*args, **kwargs):
        if not current_user.is_authenticated:
            return redirect(url_for('auth.login'))
        if current_user.role not in ('client', 'viewer'):
            return redirect(url_for('dashboard.index'))
        return f(*args, **kwargs)
    return decorated


def _get_client_company():
    """Get the company linked to the current client user"""
    return Company.query.filter(
        db.or_(
            Company.user_id == current_user.id,
            Company.client_user_id == current_user.id
        ),
        Company.is_active == True
    ).first()


@bp.route('/')
@login_required
@require_client
def index():
    """Client portal home — P&L summary, recent transactions"""
    company = _get_client_company()
    now = datetime.utcnow()
    month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

    stats = _get_client_stats(company, month_start, now) if company else {}

    recent = []
    if company:
        recent = Transaction.query.filter_by(company_id=company.id).order_by(
            Transaction.transaction_date.desc()
        ).limit(10).all()

    return render_template('portal/index.html',
        company=company,
        stats=stats,
        recent_transactions=recent,
        month_name=now.strftime('%B %Y'),
    )


@bp.route('/transactions')
@login_required
@require_client
def transactions():
    """Client transaction feed with filtering"""
    company = _get_client_company()
    if not company:
        flash('No company connected yet. Please contact your bookkeeper.', 'info')
        return render_template('portal/transactions.html', transactions=[], company=None, pagination=None, search='', status_filter='')

    page = request.args.get('page', 1, type=int)
    status = request.args.get('status', '')
    search = request.args.get('q', '').strip()

    query = Transaction.query.filter_by(company_id=company.id)
    if status:
        query = query.filter(Transaction.categorization_status == status)
    if search:
        query = query.filter(
            db.or_(
                Transaction.description.ilike(f'%{search}%'),
                Transaction.vendor_name.ilike(f'%{search}%'),
            )
        )

    pagination = query.order_by(Transaction.transaction_date.desc()).paginate(
        page=page, per_page=50, error_out=False
    )

    return render_template('portal/transactions.html',
        company=company,
        transactions=pagination.items,
        pagination=pagination,
        search=search,
        status_filter=status,
    )


@bp.route('/transactions/<int:txn_id>/flag', methods=['POST'])
@login_required
@require_client
def flag_transaction(txn_id):
    """Client flags a transaction for operator review"""
    company = _get_client_company()
    if not company:
        return jsonify({'success': False, 'error': 'No company'}), 404

    txn = Transaction.query.filter_by(id=txn_id, company_id=company.id).first_or_404()
    data = request.get_json() or {}

    txn.review_status = 'flagged'
    txn.review_notes = data.get('note', '')
    db.session.commit()

    return jsonify({'success': True, 'message': 'Transaction flagged for review'})


@bp.route('/reports')
@login_required
@require_client
def reports():
    """Client report viewer"""
    company = _get_client_company()
    return render_template('portal/reports.html', company=company)


@bp.route('/reports/download/<report_type>')
@login_required
@require_client
def download_report(report_type):
    """Download a financial report"""
    from app.routes.reports import generate_pnl_data, generate_balance_data, create_pdf_download, create_csv_download
    from flask import g
    import flask_login

    company = _get_client_company()
    if not company:
        return jsonify({'error': 'No company connected'}), 404

    fmt = request.args.get('format', 'pdf')
    now = datetime.utcnow()
    start = now.replace(day=1, month=1)
    end = now

    if report_type == 'pl':
        data = generate_pnl_data(start.strftime('%Y-%m-%d'), end.strftime('%Y-%m-%d'))
        filename = f"PL_{now.strftime('%Y%m')}"
    elif report_type == 'balance':
        data = generate_balance_data(end.strftime('%Y-%m-%d'))
        filename = f"Balance_{now.strftime('%Y%m%d')}"
    else:
        return jsonify({'error': 'Unknown report type'}), 400

    if fmt == 'pdf':
        return create_pdf_download(data, filename + '.pdf')
    return create_csv_download(data, filename + '.csv')


@bp.route('/connect-bank')
@login_required
@require_client
def connect_bank():
    """Bank connection setup via Plaid Link"""
    company = _get_client_company()
    return render_template('portal/connect_bank.html', company=company)


@bp.route('/connect-bank/token', methods=['POST'])
@login_required
@require_client
def create_link_token():
    """Create a Plaid Link token for the client"""
    try:
        from app.services.plaid_service import PlaidService
        plaid = PlaidService()
        token = plaid.create_link_token(str(current_user.id))
        return jsonify({'success': True, 'link_token': token})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@bp.route('/connect-bank/exchange', methods=['POST'])
@login_required
@require_client
def exchange_token():
    """Exchange Plaid public token for access token"""
    data = request.get_json() or {}
    public_token = data.get('public_token')
    if not public_token:
        return jsonify({'success': False, 'error': 'Missing token'}), 400

    company = _get_client_company()
    if not company:
        return jsonify({'success': False, 'error': 'No company found'}), 404

    try:
        from app.services.plaid_service import PlaidService
        from app.models.bank_connection import BankConnection
        plaid = PlaidService()
        result = plaid.exchange_public_token(public_token)
        conn = BankConnection(
            tenant_id=current_user.tenant_id,
            company_id=company.id,
            plaid_item_id=result['item_id'],
            plaid_access_token=result['access_token'],
            institution_name=data.get('institution_name', 'Bank'),
            status='active',
        )
        db.session.add(conn)
        db.session.commit()
        return jsonify({'success': True, 'message': 'Bank connected successfully'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@bp.route('/upload', methods=['GET', 'POST'])
@login_required
@require_client
def upload_statement():
    """Manual CSV bank statement upload"""
    company = _get_client_company()

    if request.method == 'POST':
        if 'file' not in request.files:
            return jsonify({'success': False, 'error': 'No file selected'}), 400

        file = request.files['file']
        if not file.filename:
            return jsonify({'success': False, 'error': 'Empty filename'}), 400

        if not company:
            return jsonify({'success': False, 'error': 'No company linked. Contact your bookkeeper.'}), 400

        try:
            imported = _parse_and_import_csv(file, company)
            return jsonify({'success': True, 'imported': imported})
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)}), 500

    return render_template('portal/upload.html', company=company)


def _parse_and_import_csv(file, company):
    """Parse a bank CSV and create Transaction records with GAAP categorization"""
    import csv, io, uuid
    from app.models.transaction import Transaction
    from app.services.gaap_coa import categorize_by_gaap

    stream = io.StringIO(file.stream.read().decode('utf-8', errors='replace'))
    reader = csv.DictReader(stream)

    DATE_COLS = ('date', 'transaction date', 'trans date', 'posting date', 'value date')
    DESC_COLS = ('description', 'memo', 'details', 'narrative', 'payee', 'transaction description')
    AMT_COLS = ('amount', 'transaction amount', 'debit/credit', 'credit', 'debit')

    def find_col(headers, candidates):
        for h in headers:
            if h.strip().lower() in candidates:
                return h
        return None

    headers = reader.fieldnames or []
    date_col = find_col(headers, DATE_COLS)
    desc_col = find_col(headers, DESC_COLS)
    amt_col = find_col(headers, AMT_COLS)

    if not (date_col and amt_col):
        raise ValueError('CSV must have Date and Amount columns')

    imported = 0
    for row in reader:
        raw_date = row.get(date_col, '').strip()
        raw_amt = row.get(amt_col, '').strip().replace(',', '').replace('$', '')
        raw_desc = row.get(desc_col, '').strip() if desc_col else ''

        if not raw_date or not raw_amt:
            continue

        try:
            from datetime import date as date_cls
            for fmt in ('%m/%d/%Y', '%Y-%m-%d', '%m-%d-%Y', '%d/%m/%Y'):
                try:
                    txn_date = datetime.strptime(raw_date, fmt).date()
                    break
                except ValueError:
                    continue
            else:
                continue
            amount = float(raw_amt)
        except (ValueError, TypeError):
            continue

        txn_id = f'csv-{uuid.uuid4().hex[:16]}'
        gaap = categorize_by_gaap(raw_desc, '', amount)

        txn = Transaction(
            company_id=company.id,
            qbo_transaction_id=txn_id,
            transaction_type='BankUpload',
            transaction_date=txn_date,
            amount=amount,
            description=raw_desc,
            vendor_name=raw_desc[:100] if raw_desc else None,
            categorization_status='suggested' if gaap else 'uncategorized',
            suggested_category=f"{gaap['account_number']} {gaap['account_name']}" if gaap else None,
            suggested_confidence=gaap['confidence'] if gaap else None,
            categorized_by='ai' if gaap else None,
        )
        db.session.add(txn)
        imported += 1

    db.session.commit()
    return imported


@bp.route('/api/stats')
@login_required
@require_client
def api_stats():
    """JSON stats for the portal dashboard"""
    company = _get_client_company()
    if not company:
        return jsonify({})
    now = datetime.utcnow()
    month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    return jsonify(_get_client_stats(company, month_start, now))


def _get_client_stats(company, period_start, period_end):
    """Compute summary stats for a company over a period"""
    if not company:
        return {}

    txns = Transaction.query.filter(
        Transaction.company_id == company.id,
        Transaction.transaction_date >= period_start.date(),
        Transaction.transaction_date <= period_end.date(),
    ).all()

    total_income = sum(float(t.amount) for t in txns if t.amount and float(t.amount) > 0)
    total_expenses = sum(abs(float(t.amount)) for t in txns if t.amount and float(t.amount) < 0)
    uncategorized = sum(1 for t in txns if t.categorization_status == 'uncategorized')

    return {
        'total_income': round(total_income, 2),
        'total_expenses': round(total_expenses, 2),
        'net': round(total_income - total_expenses, 2),
        'transaction_count': len(txns),
        'uncategorized_count': uncategorized,
    }
