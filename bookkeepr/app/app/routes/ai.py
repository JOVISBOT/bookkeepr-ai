"""
AI Routes for BookKeepr
Auto-categorization and intelligent features
"""
from flask import Blueprint, jsonify, request
from flask_login import login_required, current_user
from app.models.transaction import Transaction
from app.models.company import Company
from extensions import db

bp = Blueprint('ai', __name__, url_prefix='/api/v1/ai')


@bp.route('/categorize', methods=['POST'])
@login_required
def categorize_transactions():
    """Batch-categorize all uncategorized transactions using local classifier."""
    from app.services.local_classifier import classify as local_classify

    companies = Company.query.filter_by(user_id=current_user.id).all()
    company_ids = [c.id for c in companies]

    transactions = Transaction.query.filter(
        Transaction.company_id.in_(company_ids),
        Transaction.categorization_status.in_(['uncategorized', 'suggested'])
    ).all()

    if not transactions:
        return jsonify({'message': 'No uncategorized transactions found', 'categorized': 0})

    categorized_count = 0
    for txn in transactions:
        result = local_classify(
            txn.description or '',
            txn.vendor_name or '',
            float(txn.amount or 0),
            txn.company_id,
        )
        label = result['category']
        confidence = result['confidence']
        txn.suggested_category = label
        txn.suggested_confidence = confidence
        txn.categorized_by = 'ai'
        if confidence >= 80:
            txn.category = label
            txn.categorization_status = 'categorized'
            categorized_count += 1
        else:
            txn.categorization_status = 'suggested'
        raw = txn.raw_data or {}
        raw['ai_explanation'] = result.get('explanation', label)
        raw['classification_source'] = result.get('source', 'unknown')
        txn.raw_data = raw

    db.session.commit()
    return jsonify({
        'message': f'Categorized {categorized_count} of {len(transactions)} transactions',
        'categorized': categorized_count,
        'total': len(transactions),
    })


@bp.route('/suggestions', methods=['GET'])
@login_required
def get_suggestions():
    """Get classifier suggestions for uncategorized transactions."""
    from app.services.local_classifier import classify as local_classify

    companies = Company.query.filter_by(user_id=current_user.id).all()
    company_ids = [c.id for c in companies]

    transactions = Transaction.query.filter(
        Transaction.company_id.in_(company_ids),
        Transaction.categorization_status == 'uncategorized',
    ).limit(10).all()

    suggestions = []
    for txn in transactions:
        result = local_classify(
            txn.description or '',
            txn.vendor_name or '',
            float(txn.amount or 0),
            txn.company_id,
        )
        suggestions.append({
            'id': txn.id,
            'description': txn.description,
            'suggested_category': result['category'],
            'confidence': result['confidence'],
            'source': result['source'],
            'explanation': result.get('explanation', ''),
            'amount': float(txn.amount or 0),
        })

    return jsonify({'suggestions': suggestions, 'count': len(suggestions)})


@bp.route('/stats', methods=['GET'])
@login_required
def get_ai_stats():
    """Categorization statistics."""
    companies = Company.query.filter_by(user_id=current_user.id).all()
    company_ids = [c.id for c in companies]

    total = Transaction.query.filter(Transaction.company_id.in_(company_ids)).count()
    categorized = Transaction.query.filter(
        Transaction.company_id.in_(company_ids),
        Transaction.category.isnot(None),
    ).count()
    uncategorized = total - categorized

    return jsonify({
        'total_transactions': total,
        'categorized': categorized,
        'uncategorized': uncategorized,
        'percentage': round((categorized / total * 100), 1) if total > 0 else 0,
    })


@bp.route('/anomalies', methods=['GET'])
@login_required
def detect_anomalies():
    """Rule-based anomaly detection — no AI API needed."""
    from sqlalchemy import text as sa_text
    from collections import defaultdict

    company = Company.query.filter_by(user_id=current_user.id, is_active=True).first()
    if not company:
        return jsonify({'anomalies': [], 'summary': {}})

    anomalies = []

    # 1. Duplicate detection: same vendor + amount within 3 days
    dup_rows = db.session.execute(sa_text('''
        SELECT a.id as id1, b.id as id2,
               a.vendor_name, a.amount, a.transaction_date as date1, b.transaction_date as date2
        FROM transactions a
        JOIN transactions b ON a.company_id = b.company_id
          AND a.vendor_name = b.vendor_name
          AND a.amount = b.amount
          AND a.id < b.id
          AND ABS(julianday(a.transaction_date) - julianday(b.transaction_date)) <= 3
        WHERE a.company_id = :cid
        LIMIT 20
    '''), {'cid': company.id}).fetchall()

    for r in dup_rows:
        anomalies.append({
            'type': 'duplicate',
            'severity': 'high',
            'title': f'Possible duplicate: {r.vendor_name}',
            'detail': f'Same amount ${abs(float(r.amount)):.2f} on {r.date1} and {r.date2}',
            'transaction_ids': [r.id1, r.id2],
        })

    # 2. Amount outliers: transactions > 3× the vendor's average
    outlier_rows = db.session.execute(sa_text('''
        SELECT t.id, t.vendor_name, t.amount, t.transaction_date,
               AVG(t2.amount) as avg_amt, COUNT(t2.id) as cnt
        FROM transactions t
        JOIN transactions t2 ON t.vendor_name = t2.vendor_name
          AND t.company_id = t2.company_id
          AND t2.id != t.id
        WHERE t.company_id = :cid
          AND t.amount < 0
          AND t2.amount < 0
        GROUP BY t.id
        HAVING cnt >= 3
          AND ABS(t.amount) > ABS(avg_amt) * 3
        ORDER BY ABS(t.amount) DESC
        LIMIT 10
    '''), {'cid': company.id}).fetchall()

    for r in outlier_rows:
        anomalies.append({
            'type': 'amount_outlier',
            'severity': 'medium',
            'title': f'Unusual amount: {r.vendor_name}',
            'detail': f'${abs(float(r.amount)):.2f} vs typical ${abs(float(r.avg_amt)):.2f} avg ({r.cnt} transactions)',
            'transaction_ids': [r.id],
        })

    # 3. Weekend/holiday charges for B2B vendors (simple heuristic)
    weekend_rows = db.session.execute(sa_text('''
        SELECT id, vendor_name, amount, transaction_date
        FROM transactions
        WHERE company_id = :cid
          AND amount < 0
          AND strftime('%w', transaction_date) IN ('0', '6')
          AND ABS(amount) > 500
        ORDER BY ABS(amount) DESC
        LIMIT 10
    '''), {'cid': company.id}).fetchall()

    for r in weekend_rows:
        anomalies.append({
            'type': 'weekend_charge',
            'severity': 'low',
            'title': f'Weekend charge: {r.vendor_name or "Unknown"}',
            'detail': f'${abs(float(r.amount)):.2f} on {r.transaction_date} (weekend)',
            'transaction_ids': [r.id],
        })

    summary = {
        'total': len(anomalies),
        'high': sum(1 for a in anomalies if a['severity'] == 'high'),
        'medium': sum(1 for a in anomalies if a['severity'] == 'medium'),
        'low': sum(1 for a in anomalies if a['severity'] == 'low'),
    }
    return jsonify({'anomalies': anomalies, 'summary': summary})
