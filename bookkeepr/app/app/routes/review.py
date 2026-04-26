"""Human-in-the-Loop Review Routes"""
from datetime import datetime
from flask import Blueprint, render_template, request, jsonify, flash, redirect, url_for
from flask_login import login_required, current_user
from sqlalchemy import func

from extensions import db
from app.models.transaction import Transaction
from app.models.company import Company

bp = Blueprint('review', __name__)


@bp.route('/review')
@login_required
def index():
    """Review queue for AI categorizations"""
    company = Company.query.filter_by(user_id=current_user.id).first()
    
    # Stats
    stats = {
        'pending_review': 0,
        'approved_today': 0,
        'rejected_today': 0,
        'accuracy_rate': 0,
    }
    
    transactions = []
    if company:
        # Only show transactions with AI suggestions awaiting review
        transactions = Transaction.query.filter_by(
            company_id=company.id,
            categorization_status='suggested',
            review_status='pending'
        ).order_by(Transaction.suggested_confidence.desc()).limit(50).all()
        
        # Stats
        stats['pending_review'] = Transaction.query.filter_by(
            company_id=company.id,
            categorization_status='suggested',
            review_status='pending'
        ).count()
        
        today = datetime.utcnow().date()
        stats['approved_today'] = Transaction.query.filter(
            Transaction.company_id == company.id,
            Transaction.review_status == 'approved',
            func.date(Transaction.reviewed_at) == today
        ).count()
        
        stats['rejected_today'] = Transaction.query.filter(
            Transaction.company_id == company.id,
            Transaction.review_status == 'rejected',
            func.date(Transaction.reviewed_at) == today
        ).count()
        
        # Calculate accuracy: approved / (approved + rejected) for AI suggestions
        total_reviewed = stats['approved_today'] + stats['rejected_today']
        if total_reviewed > 0:
            stats['accuracy_rate'] = round((stats['approved_today'] / total_reviewed) * 100, 1)
    
    return render_template('review.html', transactions=transactions, stats=stats)


@bp.route('/review/approve/<int:transaction_id>', methods=['POST'])
@login_required
def approve(transaction_id):
    """Approve AI categorization suggestion"""
    company = Company.query.filter_by(user_id=current_user.id).first()
    if not company:
        return jsonify({'success': False, 'error': 'No company found'}), 404
    
    txn = Transaction.query.filter_by(
        id=transaction_id,
        company_id=company.id
    ).first()
    
    if not txn:
        return jsonify({'success': False, 'error': 'Transaction not found'}), 404
    
    if txn.categorization_status != 'suggested':
        return jsonify({'success': False, 'error': 'No suggestion to approve'}), 400
    
    # Promote suggestion to final category
    txn.category = txn.suggested_category
    txn.categorization_status = 'categorized'
    txn.categorized_by = 'user'
    txn.categorized_at = datetime.utcnow()
    txn.review_status = 'approved'
    txn.reviewed_by_user_id = current_user.id
    txn.reviewed_at = datetime.utcnow()
    
    db.session.commit()
    
    return jsonify({
        'success': True,
        'transaction_id': transaction_id,
        'category': txn.category,
        'message': 'Categorization approved'
    })


@bp.route('/review/reject/<int:transaction_id>', methods=['POST'])
@login_required
def reject(transaction_id):
    """Reject AI categorization and optionally provide correct category"""
    company = Company.query.filter_by(user_id=current_user.id).first()
    if not company:
        return jsonify({'success': False, 'error': 'No company found'}), 404
    
    txn = Transaction.query.filter_by(
        id=transaction_id,
        company_id=company.id
    ).first()
    
    if not txn:
        return jsonify({'success': False, 'error': 'Transaction not found'}), 404
    
    data = request.get_json() or {}
    correct_category = data.get('correct_category', '').strip()
    
    # Mark as rejected
    txn.review_status = 'rejected'
    txn.reviewed_by_user_id = current_user.id
    txn.reviewed_at = datetime.utcnow()
    txn.review_notes = data.get('notes', '')
    
    # If correct category provided, apply it
    if correct_category:
        txn.category = correct_category
        txn.categorization_status = 'categorized'
        txn.categorized_by = 'user_corrected'
        txn.categorized_at = datetime.utcnow()
    else:
        # Reset to uncategorized for re-processing
        txn.categorization_status = 'uncategorized'
        txn.suggested_category = None
        txn.suggested_confidence = None
        txn.categorized_by = None
    
    db.session.commit()
    
    return jsonify({
        'success': True,
        'transaction_id': transaction_id,
        'category': correct_category or 'Reset to uncategorized',
        'message': 'Categorization rejected and corrected'
    })


@bp.route('/review/batch-approve', methods=['POST'])
@login_required
def batch_approve():
    """Batch approve multiple transactions"""
    company = Company.query.filter_by(user_id=current_user.id).first()
    if not company:
        return jsonify({'success': False, 'error': 'No company found'}), 404
    
    data = request.get_json() or {}
    transaction_ids = data.get('transaction_ids', [])
    
    if not transaction_ids:
        return jsonify({'success': False, 'error': 'No transaction IDs provided'}), 400
    
    count = 0
    for txn_id in transaction_ids:
        txn = Transaction.query.filter_by(
            id=txn_id,
            company_id=company.id,
            categorization_status='suggested',
            review_status='pending'
        ).first()
        
        if txn:
            txn.category = txn.suggested_category
            txn.categorization_status = 'categorized'
            txn.categorized_by = 'user'
            txn.categorized_at = datetime.utcnow()
            txn.review_status = 'approved'
            txn.reviewed_by_user_id = current_user.id
            txn.reviewed_at = datetime.utcnow()
            count += 1
    
    db.session.commit()
    
    return jsonify({
        'success': True,
        'approved_count': count,
        'message': f'{count} transactions approved'
    })


@bp.route('/review/metrics')
@login_required
def metrics():
    """Get review accuracy metrics for the current user"""
    company = Company.query.filter_by(user_id=current_user.id).first()
    if not company:
        return jsonify({'error': 'No company found'}), 404
    
    # Overall stats
    total_suggested = Transaction.query.filter_by(
        company_id=company.id,
        categorized_by='ai'
    ).count()
    
    total_approved = Transaction.query.filter_by(
        company_id=company.id,
        review_status='approved'
    ).count()
    
    total_rejected = Transaction.query.filter_by(
        company_id=company.id,
        review_status='rejected'
    ).count()
    
    total_reviewed = total_approved + total_rejected
    accuracy = round((total_approved / total_reviewed) * 100, 1) if total_reviewed > 0 else 0
    
    # Daily breakdown (last 7 days)
    from sqlalchemy import func
    daily_stats = db.session.query(
        func.date(Transaction.reviewed_at).label('date'),
        func.count().label('total'),
        func.sum(func.case((Transaction.review_status == 'approved', 1), else_=0)).label('approved'),
        func.sum(func.case((Transaction.review_status == 'rejected', 1), else_=0)).label('rejected')
    ).filter(
        Transaction.company_id == company.id,
        Transaction.reviewed_at.isnot(None)
    ).group_by(
        func.date(Transaction.reviewed_at)
    ).order_by(
        func.date(Transaction.reviewed_at).desc()
    ).limit(7).all()
    
    return jsonify({
        'total_suggested': total_suggested,
        'total_approved': total_approved,
        'total_rejected': total_rejected,
        'accuracy_rate': accuracy,
        'pending_review': Transaction.query.filter_by(
            company_id=company.id,
            categorization_status='suggested',
            review_status='pending'
        ).count(),
        'daily_breakdown': [
            {
                'date': str(row.date),
                'total': row.total,
                'approved': int(row.approved or 0),
                'rejected': int(row.rejected or 0),
                'accuracy': round((int(row.approved or 0) / row.total) * 100, 1) if row.total > 0 else 0
            }
            for row in daily_stats
        ]
    })
