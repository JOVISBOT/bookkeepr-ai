"""Admin Dashboard Routes"""
from datetime import datetime, timedelta
from flask import Blueprint, render_template, jsonify, request
from flask_login import login_required, current_user
from sqlalchemy import func, desc

from extensions import db
from app.models.user import User
from app.models.company import Company
from app.models.transaction import Transaction
from app.models.subscription import UserSubscription

bp = Blueprint('admin', __name__)


def admin_required(f):
    """Decorator to require admin access"""
    from functools import wraps
    
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            return jsonify({'error': 'Admin access required'}), 403
        return f(*args, **kwargs)
    return decorated_function


@bp.route('/admin')
@login_required
@admin_required
def index():
    """Admin dashboard"""
    # System stats
    stats = {
        'total_users': User.query.count(),
        'active_users': User.query.filter_by(is_active=True).count(),
        'total_companies': Company.query.count(),
        'connected_companies': Company.query.filter_by(is_connected=True).count(),
        'total_transactions': Transaction.query.count(),
        'transactions_today': Transaction.query.filter(
            func.date(Transaction.created_at) == datetime.utcnow().date()
        ).count(),
        'pending_reviews': Transaction.query.filter_by(review_status='pending').count(),
    }
    
    # Recent users
    recent_users = User.query.order_by(desc(User.created_at)).limit(10).all()
    
    # Recent transactions
    recent_transactions = Transaction.query.order_by(desc(Transaction.created_at)).limit(20).all()
    
    # Daily transaction counts (last 30 days)
    daily_counts = db.session.query(
        func.date(Transaction.created_at).label('date'),
        func.count().label('count')
    ).filter(
        Transaction.created_at >= datetime.utcnow() - timedelta(days=30)
    ).group_by(
        func.date(Transaction.created_at)
    ).order_by(
        func.date(Transaction.created_at)
    ).all()
    
    # AI accuracy over time
    ai_accuracy = db.session.query(
        func.date(Transaction.categorized_at).label('date'),
        func.count().label('total'),
        func.sum(func.case((Transaction.review_status == 'approved', 1), else_=0)).label('approved')
    ).filter(
        Transaction.categorized_by == 'ai',
        Transaction.categorized_at >= datetime.utcnow() - timedelta(days=30)
    ).group_by(
        func.date(Transaction.categorized_at)
    ).order_by(
        func.date(Transaction.categorized_at)
    ).all()
    
    return render_template('admin.html',
        stats=stats,
        recent_users=recent_users,
        recent_transactions=recent_transactions,
        daily_counts=daily_counts,
        ai_accuracy=ai_accuracy,
    )


@bp.route('/admin/users')
@login_required
@admin_required
def users():
    """List all users"""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 50, type=int)
    
    users = User.query.order_by(desc(User.created_at)).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    return jsonify({
        'users': [u.to_dict() for u in users.items],
        'total': users.total,
        'pages': users.pages,
        'current_page': page
    })


@bp.route('/admin/users/<int:user_id>', methods=['GET', 'PUT'])
@login_required
@admin_required
def user_detail(user_id):
    """Get or update user details"""
    user = User.query.get_or_404(user_id)
    
    if request.method == 'GET':
        return jsonify(user.to_dict())
    
    data = request.get_json() or {}
    
    if 'is_active' in data:
        user.is_active = bool(data['is_active'])
    if 'is_admin' in data:
        user.is_admin = bool(data['is_admin'])
    
    db.session.commit()
    return jsonify({'success': True, 'user': user.to_dict()})


@bp.route('/admin/transactions')
@login_required
@admin_required
def transactions():
    """List all transactions"""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 100, type=int)
    company_id = request.args.get('company_id', type=int)
    
    query = Transaction.query
    if company_id:
        query = query.filter_by(company_id=company_id)
    
    transactions = query.order_by(desc(Transaction.created_at)).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    return jsonify({
        'transactions': [t.to_dict() for t in transactions.items],
        'total': transactions.total,
        'pages': transactions.pages,
        'current_page': page
    })


@bp.route('/admin/stats')
@login_required
@admin_required
def stats():
    """Get system health metrics"""
    # Revenue (placeholder - would come from Stripe)
    revenue_stats = {
        'mrr': 0,  # Monthly Recurring Revenue
        'arr': 0,  # Annual Recurring Revenue
        'trial_users': UserSubscription.query.filter_by(status='trialing').count() if 'UserSubscription' in dir() else 0,
    }
    
    # System health
    db_health = _check_db_health()
    
    # Transaction categorization stats
    categorization_stats = {
        'total_categorized': Transaction.query.filter(
            Transaction.categorization_status.in_(['categorized', 'suggested'])
        ).count(),
        'ai_categorized': Transaction.query.filter_by(categorized_by='ai').count(),
        'user_categorized': Transaction.query.filter_by(categorized_by='user').count(),
        'uncategorized': Transaction.query.filter_by(categorization_status='uncategorized').count(),
    }
    
    return jsonify({
        'revenue': revenue_stats,
        'database': db_health,
        'categorization': categorization_stats,
        'timestamp': datetime.utcnow().isoformat(),
    })


@bp.route('/admin/ai-accuracy')
@login_required
@admin_required
def ai_accuracy():
    """Get AI accuracy metrics over time"""
    days = request.args.get('days', 30, type=int)
    cutoff = datetime.utcnow() - timedelta(days=days)
    
    # Overall accuracy
    total_ai = Transaction.query.filter(
        Transaction.categorized_by == 'ai',
        Transaction.categorized_at >= cutoff
    ).count()
    
    approved_ai = Transaction.query.filter(
        Transaction.categorized_by == 'ai',
        Transaction.review_status == 'approved',
        Transaction.categorized_at >= cutoff
    ).count()
    
    rejected_ai = Transaction.query.filter(
        Transaction.categorized_by == 'ai',
        Transaction.review_status == 'rejected',
        Transaction.categorized_at >= cutoff
    ).count()
    
    # By category accuracy
    by_category = db.session.query(
        Transaction.suggested_category,
        func.count().label('total'),
        func.sum(func.case((Transaction.review_status == 'approved', 1), else_=0)).label('approved'),
        func.sum(func.case((Transaction.review_status == 'rejected', 1), else_=0)).label('rejected')
    ).filter(
        Transaction.categorized_by == 'ai',
        Transaction.categorized_at >= cutoff,
        Transaction.suggested_category.isnot(None)
    ).group_by(
        Transaction.suggested_category
    ).all()
    
    return jsonify({
        'overall': {
            'total': total_ai,
            'approved': approved_ai,
            'rejected': rejected_ai,
            'accuracy': round((approved_ai / (approved_ai + rejected_ai)) * 100, 1) if (approved_ai + rejected_ai) > 0 else 0,
        },
        'by_category': [
            {
                'category': row.suggested_category,
                'total': row.total,
                'approved': int(row.approved or 0),
                'rejected': int(row.rejected or 0),
                'accuracy': round((int(row.approved or 0) / row.total) * 100, 1) if row.total > 0 else 0,
            }
            for row in by_category
        ],
        'period': f'Last {days} days',
    })


def _check_db_health():
    """Check database health"""
    try:
        # Test connection
        db.session.execute('SELECT 1')
        
        # Get table sizes
        from sqlalchemy import inspect
        inspector = inspect(db.engine)
        
        table_info = []
        for table_name in inspector.get_table_names():
            try:
                count = db.session.execute(f"SELECT COUNT(*) FROM {table_name}").scalar()
                table_info.append({'name': table_name, 'rows': count})
            except:
                table_info.append({'name': table_name, 'rows': -1})
        
        return {
            'status': 'healthy',
            'tables': table_info,
        }
    except Exception as e:
        return {
            'status': 'error',
            'error': str(e),
        }
