"""Billing and Subscription Management Routes"""
from datetime import datetime, timedelta
from flask import Blueprint, render_template, jsonify, request
from flask_login import login_required, current_user

from extensions import db
from app.models.subscription import SubscriptionPlan, UserSubscription, BillingInvoice

bp = Blueprint('billing', __name__, url_prefix='/billing')


@bp.route('/plans')
@login_required
def get_plans():
    """Billing page - show current plan, usage, upgrade options"""
    subscription = UserSubscription.query.filter_by(user_id=current_user.id).first()
    
    # Default plan if no subscription
    if not subscription:
        plan = SubscriptionPlan.query.filter_by(name='starter').first()
        if not plan:
            plan = _create_default_plans()
        subscription = _create_trial_subscription(current_user.id, plan.id)
    
    # Get invoices
    invoices = BillingInvoice.query.filter_by(user_id=current_user.id).order_by(
        BillingInvoice.created_at.desc()
    ).limit(12).all()
    
    # All plans for upgrade comparison
    all_plans = SubscriptionPlan.query.filter_by(is_active=True).order_by(
        SubscriptionPlan.price_monthly
    ).all()
    
    return render_template('billing.html', 
        subscription=subscription,
        invoices=invoices,
        all_plans=all_plans
    )


@bp.route('/subscribe', methods=['POST'])
@login_required
def subscribe():
    """Create subscription (Stripe scaffold)"""
    data = request.get_json() or {}
    plan_id = data.get('plan_id')
    billing_cycle = data.get('billing_cycle', 'monthly')
    
    if not plan_id:
        return jsonify({'success': False, 'error': 'Plan ID required'}), 400
    
    plan = SubscriptionPlan.query.get(plan_id)
    if not plan:
        return jsonify({'success': False, 'error': 'Plan not found'}), 404
    
    # TODO: Integrate with Stripe
    # For now, create a trial subscription
    subscription = UserSubscription.query.filter_by(user_id=current_user.id).first()
    
    if subscription:
        subscription.plan_id = plan.id
        subscription.billing_cycle = billing_cycle
        subscription.status = 'active'
        subscription.current_period_start = datetime.utcnow()
        subscription.current_period_end = datetime.utcnow() + timedelta(days=30)
    else:
        subscription = UserSubscription(
            user_id=current_user.id,
            plan_id=plan.id,
            billing_cycle=billing_cycle,
            status='active',
            current_period_start=datetime.utcnow(),
            current_period_end=datetime.utcnow() + timedelta(days=30)
        )
        db.session.add(subscription)
    
    db.session.commit()
    
    return jsonify({
        'success': True,
        'message': f'Subscribed to {plan.display_name} plan',
        'subscription': subscription.to_dict()
    })


@bp.route('/cancel', methods=['POST'])
@login_required
def cancel():
    """Cancel subscription at period end"""
    subscription = UserSubscription.query.filter_by(user_id=current_user.id).first()
    
    if not subscription:
        return jsonify({'success': False, 'error': 'No active subscription'}), 404
    
    subscription.cancel_at_period_end = True
    subscription.status = 'canceled'
    subscription.canceled_at = datetime.utcnow()
    db.session.commit()
    
    return jsonify({
        'success': True,
        'message': 'Subscription will cancel at end of period',
        'current_period_end': subscription.current_period_end.isoformat() if subscription.current_period_end else None
    })


@bp.route('/usage')
@login_required
def usage():
    """Get current usage stats"""
    subscription = UserSubscription.query.filter_by(user_id=current_user.id).first()
    
    if not subscription or not subscription.plan:
        return jsonify({'error': 'No subscription found'}), 404
    
    plan = subscription.plan
    used = subscription.transactions_used_this_period
    limit = plan.max_transactions
    
    return jsonify({
        'transactions_used': used,
        'transactions_limit': limit,
        'percentage': round((used / limit) * 100, 1) if limit > 0 else 0,
        'remaining': max(0, limit - used),
        'period_end': subscription.current_period_end.isoformat() if subscription.current_period_end else None,
    })


@bp.route('/invoices')
@login_required
def list_invoices():
    """List invoice history"""
    invoices = BillingInvoice.query.filter_by(user_id=current_user.id).order_by(
        BillingInvoice.created_at.desc()
    ).all()
    
    return jsonify({
        'invoices': [inv.to_dict() for inv in invoices],
        'total': len(invoices)
    })


@bp.route('/webhook', methods=['POST'])
def stripe_webhook():
    """Stripe webhook handler (placeholder)"""
    # TODO: Implement Stripe webhook signature verification
    # and handle events: invoice.paid, invoice.payment_failed, etc.
    return jsonify({'status': 'received'}), 200


def _create_default_plans():
    """Create default subscription plans if they don't exist"""
    plans = [
        SubscriptionPlan(
            name='starter',
            display_name='Starter',
            price_monthly=199,
            price_yearly=1990,
            max_transactions=1000,
            max_companies=1,
            max_users=1,
            has_ai_categorization=True,
            has_anomaly_detection=False,
            has_cashflow_forecasting=False,
            has_advanced_reports=False,
            has_api_access=False,
            has_priority_support=False,
            has_dedicated_manager=False,
        ),
        SubscriptionPlan(
            name='pro',
            display_name='Pro',
            price_monthly=499,
            price_yearly=4990,
            max_transactions=5000,
            max_companies=3,
            max_users=3,
            has_ai_categorization=True,
            has_anomaly_detection=True,
            has_cashflow_forecasting=False,
            has_advanced_reports=True,
            has_api_access=False,
            has_priority_support=True,
            has_dedicated_manager=False,
        ),
        SubscriptionPlan(
            name='business',
            display_name='Business',
            price_monthly=999,
            price_yearly=9990,
            max_transactions=25000,
            max_companies=10,
            max_users=10,
            has_ai_categorization=True,
            has_anomaly_detection=True,
            has_cashflow_forecasting=True,
            has_advanced_reports=True,
            has_api_access=True,
            has_priority_support=True,
            has_dedicated_manager=False,
        ),
        SubscriptionPlan(
            name='enterprise',
            display_name='Enterprise',
            price_monthly=2499,
            price_yearly=24990,
            max_transactions=0,  # Unlimited
            max_companies=0,  # Unlimited
            max_users=0,  # Unlimited
            has_ai_categorization=True,
            has_anomaly_detection=True,
            has_cashflow_forecasting=True,
            has_advanced_reports=True,
            has_api_access=True,
            has_priority_support=True,
            has_dedicated_manager=True,
        ),
    ]
    
    for plan in plans:
        existing = SubscriptionPlan.query.filter_by(name=plan.name).first()
        if not existing:
            db.session.add(plan)
    
    db.session.commit()
    return plans[0]


def _create_trial_subscription(user_id, plan_id):
    """Create a trial subscription for new users"""
    subscription = UserSubscription(
        user_id=user_id,
        plan_id=plan_id,
        billing_cycle='monthly',
        status='trialing',
        current_period_start=datetime.utcnow(),
        current_period_end=datetime.utcnow() + timedelta(days=14)
    )
    db.session.add(subscription)
    db.session.commit()
    return subscription
