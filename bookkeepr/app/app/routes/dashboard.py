"""Dashboard Routes"""
from datetime import datetime
from flask import Blueprint, render_template, flash, current_app, jsonify
from flask_login import login_required, current_user
from sqlalchemy import func, case
from app.models.company import Company
from app.models.transaction import Transaction
from app.models.account import Account
from app.models.subscription import UserSubscription
from extensions import db

bp = Blueprint('dashboard', __name__)


@bp.route('/')
@login_required
def index():
    """Main dashboard with premium features"""
    from flask import request
    
    # All active clients for this user (for selector)
    all_clients = Company.query.filter_by(
        user_id=current_user.id,
        is_active=True,
    ).order_by(Company.qbo_company_name).all()
    
    # Selected client (via ?client_id= or default to first connected)
    selected_id = request.args.get('client_id', type=int)
    company = None
    if selected_id:
        company = Company.query.filter_by(id=selected_id, user_id=current_user.id).first()
    if not company:
        # Prefer connected company
        company = Company.query.filter_by(
            user_id=current_user.id,
            is_active=True,
            is_connected=True,
        ).first()
    if not company:
        company = all_clients[0] if all_clients else None
    
    # Get subscription
    subscription = UserSubscription.query.filter_by(user_id=current_user.id).first()
    
    stats = {}
    transactions = []
    if company:
        month_start = datetime.utcnow().replace(day=1, hour=0, minute=0, second=0, microsecond=0).date()
        row = Transaction.query.with_entities(
            func.count().label('total'),
            func.sum(case((Transaction.transaction_date >= month_start, 1), else_=0)).label('month'),
            func.sum(case((Transaction.categorization_status == 'uncategorized', 1), else_=0)).label('uncategorized'),
            func.sum(case((Transaction.review_status == 'pending', 1), else_=0)).label('pending'),
            func.sum(case((Transaction.categorized_by == 'ai', 1), else_=0)).label('ai_count'),
        ).filter(Transaction.company_id == company.id).one()

        total = row.total or 0
        ai_count = row.ai_count or 0
        stats = {
            'total_transactions': total,
            'month_transactions': row.month or 0,
            'uncategorized_count': row.uncategorized or 0,
            'pending_count': row.pending or 0,
            'auto_categorized_count': ai_count,
            'auto_categorization_rate': round((ai_count / total) * 100, 1) if total else 0,
            'last_sync_at': company.last_sync_at,
        }
        transactions = Transaction.query.filter_by(company_id=company.id).order_by(
            Transaction.transaction_date.desc()
        ).limit(10).all()

        # Chart data: top 8 categories by spend
        from sqlalchemy import text as sa_text
        cat_rows = db.session.execute(sa_text('''
            SELECT category, COUNT(*) as cnt,
                   SUM(CASE WHEN amount < 0 THEN ABS(amount) ELSE 0 END) as spend
            FROM transactions
            WHERE company_id = :cid AND category IS NOT NULL AND category != ""
            GROUP BY category ORDER BY cnt DESC LIMIT 8
        '''), {'cid': company.id}).fetchall()
        category_labels = [r[0] for r in cat_rows]
        category_counts = [r[1] for r in cat_rows]
        category_spend  = [round(float(r[2]), 2) for r in cat_rows]

        # Chart data: last 6 months income vs expenses
        monthly_rows = db.session.execute(sa_text('''
            SELECT strftime('%Y-%m', transaction_date) as mo,
                   SUM(CASE WHEN amount > 0 THEN amount ELSE 0 END) as income,
                   SUM(CASE WHEN amount < 0 THEN ABS(amount) ELSE 0 END) as expenses
            FROM transactions
            WHERE company_id = :cid
              AND transaction_date >= date('now', '-6 months')
            GROUP BY mo ORDER BY mo
        '''), {'cid': company.id}).fetchall()
        monthly_labels   = [r[0] for r in monthly_rows]
        monthly_income   = [round(float(r[1]), 2) for r in monthly_rows]
        monthly_expenses = [round(float(r[2]), 2) for r in monthly_rows]
    else:
        category_labels = category_counts = category_spend = []
        monthly_labels = monthly_income = monthly_expenses = []

    return render_template('dashboard/index.html',
        company=company,
        all_clients=all_clients,
        stats=stats,
        transactions=transactions,
        subscription=subscription,
        category_labels=category_labels,
        category_counts=category_counts,
        category_spend=category_spend,
        monthly_labels=monthly_labels,
        monthly_income=monthly_income,
        monthly_expenses=monthly_expenses,
    )


@bp.route('/transactions')
@login_required
def transactions():
    """Transaction list - actually load data"""
    from flask import request
    
    # Pick connected company or first active
    company = Company.query.filter_by(
        user_id=current_user.id,
        is_active=True,
        is_connected=True,
    ).first()
    if not company:
        company = Company.query.filter_by(user_id=current_user.id, is_active=True).first()
    
    transactions_list = []
    total = 0
    if company:
        # Apply filters from query string
        q = Transaction.query.filter_by(company_id=company.id)
        
        search = request.args.get('search', '').strip()
        if search:
            q = q.filter(Transaction.description.ilike(f'%{search}%'))
        
        category_filter = request.args.get('category', '').strip()
        if category_filter == 'uncategorized':
            q = q.filter_by(categorization_status='uncategorized')
        elif category_filter == 'categorized':
            q = q.filter(Transaction.categorization_status != 'uncategorized')
        
        status_filter = request.args.get('status', '').strip()
        if status_filter == 'needs_review':
            q = q.filter_by(review_status='pending')
        elif status_filter == 'approved':
            q = q.filter_by(review_status='approved')
        
        total = q.count()
        transactions_list = q.order_by(Transaction.transaction_date.desc()).limit(200).all()
    
    return render_template('dashboard/transactions.html',
                           transactions=transactions_list,
                           total=total,
                           company=company)


@bp.route('/transactions/<int:transaction_id>')
@login_required
def transaction_detail(transaction_id):
    """Transaction detail / edit view"""
    txn = Transaction.query.get_or_404(transaction_id)
    company = Company.query.filter_by(id=txn.company_id, user_id=current_user.id).first()
    if not company:
        from flask import abort
        abort(403)
    accounts = Account.query.filter_by(company_id=company.id, is_active=True).order_by(Account.account_number, Account.name).all()
    # Distinct vendors from this company's transactions
    from sqlalchemy import distinct
    vendor_rows = db.session.query(distinct(Transaction.vendor_name)).filter(
        Transaction.company_id == company.id,
        Transaction.vendor_name.isnot(None),
        Transaction.vendor_name != ''
    ).order_by(Transaction.vendor_name).all()
    vendors = [r[0] for r in vendor_rows]
    return render_template('dashboard/transaction_detail.html',
                           txn=txn, company=company, accounts=accounts, vendors=vendors)


@bp.route('/accounts')
@login_required
def accounts():
    """Chart of accounts"""
    company = Company.query.filter_by(user_id=current_user.id, is_active=True).first()
    accts = []
    if company:
        accts = Account.query.filter_by(company_id=company.id, is_active=True).order_by(
            Account.account_number, Account.name
        ).all()
    return render_template('dashboard/accounts.html', accounts=accts, company=company)


@bp.route('/reports')
@login_required
def reports():
    """Reports page"""
    return render_template('dashboard/reports.html')


@bp.route('/settings')
@login_required
def settings():
    """User settings"""
    return render_template('dashboard/settings.html')


@bp.route('/settings/company')
@login_required
def company_settings():
    """Company/QBO connection settings"""
    from app.models.company import Company
    company = Company.query.filter_by(user_id=current_user.id, is_active=True).first()
    return render_template('dashboard/company_settings.html', company=company)


@bp.route('/ai-categorize', methods=['POST'])
@login_required
def ai_categorize():
    """AJAX endpoint: run GAAP categorization on all uncategorized/suggested transactions."""
    from app.services.gaap_coa import categorize_by_gaap
    from app.models.transaction import Transaction
    from extensions import db

    company = Company.query.filter_by(user_id=current_user.id).first()
    if not company:
        return jsonify({'success': False, 'error': 'No company found'}), 404

    txns = Transaction.query.filter(
        Transaction.company_id == company.id,
        Transaction.categorization_status.in_(['uncategorized', 'suggested'])
    ).all()

    updated = 0
    from app.services.local_classifier import classify as local_classify
    for txn in txns:
        result = local_classify(txn.description or '', txn.vendor_name or '', float(txn.amount or 0), company.id)
        label = result['category']
        confidence = result['confidence']
        txn.suggested_category = label
        txn.suggested_confidence = confidence
        txn.categorized_by = 'ai'
        if confidence >= 80:
            txn.category = label
            txn.categorization_status = 'categorized'
        else:
            txn.categorization_status = 'suggested'
        raw = txn.raw_data or {}
        raw['ai_explanation'] = result.get('explanation', label)
        raw['classification_source'] = result.get('source', 'unknown')
        txn.raw_data = raw
        updated += 1

    db.session.commit()
    return jsonify({'success': True, 'updated': updated})


@bp.route('/transactions/bulk-approve', methods=['POST'])
@login_required
def bulk_approve():
    from flask import request as req
    from datetime import datetime
    data = req.get_json(force=True) or {}
    ids = data.get('ids', [])
    if not ids:
        return jsonify({'success': False, 'error': 'No IDs provided'}), 400

    company = Company.query.filter_by(user_id=current_user.id, is_active=True).first()
    if not company:
        return jsonify({'success': False, 'error': 'No company found'}), 404

    txns = Transaction.query.filter(
        Transaction.id.in_(ids),
        Transaction.company_id == company.id
    ).all()

    now = datetime.utcnow()
    updated = 0
    for txn in txns:
        txn.review_status = 'approved'
        txn.reviewed_by_user_id = current_user.id
        txn.reviewed_at = now
        if txn.categorization_status == 'suggested' and txn.suggested_category:
            txn.category = txn.suggested_category
            txn.categorization_status = 'categorized'
        updated += 1

    db.session.commit()
    return jsonify({'success': True, 'approved': updated})


@bp.route('/transactions/bulk-qb-push', methods=['POST'])
@login_required
def bulk_qb_push():
    from flask import request as req
    data = req.get_json(force=True) or {}
    ids = data.get('ids', [])
    if not ids:
        return jsonify({'success': False, 'error': 'No IDs provided'}), 400

    company = Company.query.filter_by(user_id=current_user.id, is_active=True).first()
    if not company:
        return jsonify({'success': False, 'error': 'No company found'}), 404

    if not getattr(company, 'access_token', None) or not getattr(company, 'qbo_realm_id', None):
        return jsonify({'success': False, 'error': 'QuickBooks not connected. Visit Settings → Connect QuickBooks first.'}), 400

    txns = Transaction.query.filter(
        Transaction.id.in_(ids),
        Transaction.company_id == company.id,
        Transaction.review_status == 'approved'
    ).all()

    if not txns:
        return jsonify({'success': False, 'error': 'Select approved transactions to push (approve them first)'}), 400

    pushed = 0
    errors = []
    try:
        from quickbooks import QuickBooks
        from quickbooks.objects.purchase import Purchase, PurchaseLine
        from quickbooks.objects.ref import Ref
        from app.services.qb_auth import QuickBooksAuthService

        auth = QuickBooksAuthService()
        client = QuickBooks(
            consumer_key=auth.client_id,
            consumer_secret=auth.client_secret,
            access_token=company.access_token,
            realm_id=company.qbo_realm_id,
            sandbox=getattr(auth, 'environment', 'sandbox') == 'sandbox'
        )

        for txn in txns:
            try:
                p = Purchase()
                p.PaymentType = 'Cash'
                p.TotalAmt = abs(float(txn.amount or 0))
                if txn.transaction_date:
                    p.TxnDate = txn.transaction_date.strftime('%Y-%m-%d')
                p.PrivateNote = (txn.description or '')[:999]

                line = PurchaseLine()
                line.Amount = abs(float(txn.amount or 0))
                line.DetailType = 'AccountBasedExpenseLineDetail'
                acct_ref = Ref()
                acct_ref.name = txn.category or 'Uncategorized Expense'
                line.AccountBasedExpenseLineDetail = {'AccountRef': {'name': acct_ref.name}}
                p.Line = [line]
                p.save(qb=client)

                raw = txn.raw_data or {}
                raw['qb_pushed'] = True
                txn.raw_data = raw
                pushed += 1
            except Exception as e:
                errors.append(f'#{txn.id}: {str(e)[:100]}')

        db.session.commit()
    except ImportError as e:
        return jsonify({'success': False, 'error': f'QB library error: {e}'}), 500
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

    return jsonify({'success': True, 'pushed': pushed, 'errors': errors})


@bp.route('/knowledge')
@login_required
def knowledge():
    """Classification knowledge base — what the system has learned"""
    from app.services.local_classifier import get_vendor_knowledge, get_classification_stats
    company = Company.query.filter_by(user_id=current_user.id, is_active=True).first()
    vendor_knowledge = []
    stats = {'approved_transactions': 0, 'unique_vendors': 0, 'high_confidence_vendors': 0, 'unique_categories': 0, 'coverage_pct': 0}
    if company:
        vendor_knowledge = get_vendor_knowledge(company.id)
        stats = get_classification_stats(company.id)
    return render_template('dashboard/knowledge.html', company=company, vendor_knowledge=vendor_knowledge, stats=stats)


@bp.route('/anomalies')
@login_required
def anomalies():
    """Anomaly detection dashboard"""
    company = Company.query.filter_by(user_id=current_user.id, is_active=True).first()
    return render_template('dashboard/anomalies.html', company=company)


@bp.route('/vendors')
@login_required
def vendors():
    """Vendor intelligence dashboard"""
    from sqlalchemy import text as sa_text
    company = Company.query.filter_by(user_id=current_user.id, is_active=True).first()
    vendor_data = []
    monthly_vendors = []
    if company:
        rows = db.session.execute(sa_text('''
            SELECT vendor_name,
                   COUNT(*) as txn_count,
                   SUM(ABS(amount)) as total_spend,
                   AVG(ABS(amount)) as avg_amount,
                   MAX(transaction_date) as last_txn,
                   MIN(transaction_date) as first_txn
            FROM transactions
            WHERE company_id = :cid
              AND vendor_name IS NOT NULL AND vendor_name != ''
              AND amount < 0
              AND transaction_date >= date('now', '-12 months')
            GROUP BY vendor_name
            ORDER BY total_spend DESC
            LIMIT 30
        '''), {'cid': company.id}).fetchall()
        vendor_data = [dict(r._mapping) for r in rows]

        # Monthly breakdown for top 5 vendors
        if vendor_data:
            top5 = [v['vendor_name'] for v in vendor_data[:5]]
            placeholders = ','.join([f':v{i}' for i in range(len(top5))])
            params = {'cid': company.id}
            for i, v in enumerate(top5):
                params[f'v{i}'] = v
            monthly_rows = db.session.execute(sa_text(f'''
                SELECT vendor_name,
                       strftime('%Y-%m', transaction_date) as month,
                       SUM(ABS(amount)) as spend
                FROM transactions
                WHERE company_id = :cid
                  AND vendor_name IN ({placeholders})
                  AND amount < 0
                  AND transaction_date >= date('now', '-6 months')
                GROUP BY vendor_name, month
                ORDER BY month
            '''), params).fetchall()
            monthly_vendors = [dict(r._mapping) for r in monthly_rows]

    return render_template('dashboard/vendors.html',
                           company=company,
                           vendor_data=vendor_data,
                           monthly_vendors=monthly_vendors)
