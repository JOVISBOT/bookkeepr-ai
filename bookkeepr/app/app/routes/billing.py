"""Billing and Subscription Management Routes"""
from datetime import datetime, timedelta
from flask import Blueprint, render_template, jsonify, request, redirect, url_for, flash
from flask_login import login_required, current_user

from extensions import db
from app.models.subscription import SubscriptionPlan, UserSubscription, BillingInvoice

bp = Blueprint('billing', __name__, url_prefix='/billing')


@bp.route('/plans')
@login_required
def get_plans():
    """Billing page — show current plan, usage, upgrade options."""
    subscription = UserSubscription.query.filter_by(user_id=current_user.id).first()

    if not subscription:
        plan = SubscriptionPlan.query.filter_by(name='starter').first()
        if not plan:
            plan = _create_default_plans()
        subscription = _create_trial_subscription(current_user.id, plan.id)

    invoices = BillingInvoice.query.filter_by(user_id=current_user.id).order_by(
        BillingInvoice.created_at.desc()
    ).limit(12).all()

    all_plans = SubscriptionPlan.query.filter_by(is_active=True).order_by(
        SubscriptionPlan.price_monthly
    ).all()

    from app.services.stripe_service import stripe_enabled
    return render_template('billing.html',
        subscription=subscription,
        invoices=invoices,
        all_plans=all_plans,
        stripe_enabled=stripe_enabled(),
    )


@bp.route('/subscribe', methods=['POST'])
@login_required
def subscribe():
    """Create Stripe Checkout Session or local trial when Stripe is not configured."""
    data = request.get_json() or {}
    plan_name = data.get('plan') or data.get('plan_id')
    billing_cycle = data.get('billing_cycle', 'monthly')

    if not plan_name:
        return jsonify({'success': False, 'error': 'Plan required'}), 400

    plan = SubscriptionPlan.query.filter(
        (SubscriptionPlan.name == str(plan_name).lower()) |
        (SubscriptionPlan.id == plan_name)
    ).first()
    if not plan:
        return jsonify({'success': False, 'error': 'Plan not found'}), 404

    from app.services.stripe_service import stripe_enabled, create_checkout_session
    if stripe_enabled():
        success_url = url_for('billing.checkout_success', _external=True) + '?session_id={CHECKOUT_SESSION_ID}'
        cancel_url = url_for('billing.checkout_cancel', _external=True)
        checkout_url, err = create_checkout_session(
            current_user, plan.name, billing_cycle, success_url, cancel_url
        )
        if err:
            return jsonify({'success': False, 'error': err}), 500
        return jsonify({'success': True, 'checkout_url': checkout_url})

    # Stripe not configured — create local trial (dev/demo mode)
    subscription = UserSubscription.query.filter_by(user_id=current_user.id).first()
    if subscription:
        subscription.plan_id = plan.id
        subscription.billing_cycle = billing_cycle
        subscription.status = 'trialing'
        subscription.current_period_start = datetime.utcnow()
        subscription.current_period_end = datetime.utcnow() + timedelta(days=14)
    else:
        subscription = _create_trial_subscription(current_user.id, plan.id)

    db.session.commit()
    return jsonify({
        'success': True,
        'message': f'Trial started for {plan.display_name}',
        'subscription': subscription.to_dict(),
    })


@bp.route('/checkout/success')
@login_required
def checkout_success():
    """Stripe redirects here after successful checkout."""
    flash('Payment successful! Your subscription is now active.', 'success')
    return redirect(url_for('billing.get_plans'))


@bp.route('/checkout/cancel')
@login_required
def checkout_cancel():
    """Stripe redirects here if user abandons checkout."""
    flash('Checkout cancelled. You can upgrade any time.', 'info')
    return redirect(url_for('pricing.index'))


@bp.route('/portal')
@login_required
def portal():
    """Redirect to Stripe self-serve billing portal."""
    from app.services.stripe_service import stripe_enabled, create_billing_portal_session
    if not stripe_enabled():
        flash('Billing portal is not available in demo mode.', 'info')
        return redirect(url_for('billing.get_plans'))

    sub = UserSubscription.query.filter_by(user_id=current_user.id).first()
    if not sub or not sub.stripe_customer_id:
        flash('No billing account found. Please subscribe first.', 'error')
        return redirect(url_for('pricing.index'))

    return_url = url_for('billing.get_plans', _external=True)
    portal_url, err = create_billing_portal_session(sub.stripe_customer_id, return_url)
    if err:
        flash('Could not open billing portal. Please try again.', 'error')
        return redirect(url_for('billing.get_plans'))

    return redirect(portal_url)


@bp.route('/cancel', methods=['POST'])
@login_required
def cancel():
    """Cancel subscription at period end."""
    from app.services.stripe_service import stripe_enabled, cancel_subscription as stripe_cancel
    subscription = UserSubscription.query.filter_by(user_id=current_user.id).first()

    if not subscription:
        return jsonify({'success': False, 'error': 'No active subscription'}), 404

    if stripe_enabled() and subscription.stripe_subscription_id:
        _, err = stripe_cancel(subscription.stripe_subscription_id, at_period_end=True)
        if err:
            return jsonify({'success': False, 'error': err}), 500

    subscription.cancel_at_period_end = True
    subscription.status = 'canceled'
    subscription.canceled_at = datetime.utcnow()
    db.session.commit()

    return jsonify({
        'success': True,
        'message': 'Subscription will cancel at end of period',
        'current_period_end': subscription.current_period_end.isoformat() if subscription.current_period_end else None,
    })


@bp.route('/usage')
@login_required
def usage():
    """Current usage stats."""
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
    """Invoice history."""
    invoices = BillingInvoice.query.filter_by(user_id=current_user.id).order_by(
        BillingInvoice.created_at.desc()
    ).all()

    return jsonify({
        'invoices': [inv.to_dict() for inv in invoices],
        'total': len(invoices),
    })


@bp.route('/webhook', methods=['POST'])
def stripe_webhook():
    """Stripe webhook handler — validates signature before processing any event."""
    import os
    from flask import current_app

    webhook_secret = os.environ.get('STRIPE_WEBHOOK_SECRET')
    stripe_key = os.environ.get('STRIPE_SECRET_KEY')

    if not stripe_key or not webhook_secret:
        current_app.logger.warning('Stripe webhook called but STRIPE_SECRET_KEY/STRIPE_WEBHOOK_SECRET not set.')
        return jsonify({'error': 'Stripe not configured'}), 503

    payload = request.get_data(as_text=True)
    sig_header = request.headers.get('Stripe-Signature', '')

    try:
        import stripe
        stripe.api_key = stripe_key
        event = stripe.Webhook.construct_event(payload, sig_header, webhook_secret)
    except ValueError:
        current_app.logger.warning('Stripe webhook: invalid payload')
        return jsonify({'error': 'Invalid payload'}), 400
    except stripe.error.SignatureVerificationError:
        current_app.logger.warning('Stripe webhook: signature verification failed')
        return jsonify({'error': 'Invalid signature'}), 400

    event_type = event.get('type', '')
    current_app.logger.info('Stripe webhook received: %s', event_type)

    if event_type == 'invoice.paid':
        _handle_invoice_paid(event['data']['object'])
    elif event_type in ('invoice.payment_failed', 'invoice.payment_action_required'):
        _handle_payment_failed(event['data']['object'])
    elif event_type == 'customer.subscription.deleted':
        _handle_subscription_canceled(event['data']['object'])
    elif event_type == 'checkout.session.completed':
        _handle_checkout_completed(event['data']['object'])

    return jsonify({'status': 'ok'}), 200


def _handle_checkout_completed(session_obj):
    """Activate subscription when Checkout Session completes."""
    from flask import current_app
    stripe_sub_id = session_obj.get('subscription')
    stripe_customer_id = session_obj.get('customer')
    if not stripe_sub_id:
        return
    sub = UserSubscription.query.filter_by(stripe_customer_id=stripe_customer_id).first()
    if sub:
        sub.stripe_subscription_id = stripe_sub_id
        sub.status = 'trialing'
        db.session.commit()
        current_app.logger.info('Checkout completed — sub %s linked to customer %s', stripe_sub_id, stripe_customer_id)


def _handle_invoice_paid(invoice):
    from flask import current_app
    stripe_sub_id = invoice.get('subscription')
    if not stripe_sub_id:
        return
    sub = UserSubscription.query.filter_by(stripe_subscription_id=stripe_sub_id).first()
    if sub:
        sub.status = 'active'
        sub.transactions_used_this_period = 0
        sub.current_period_start = datetime.utcfromtimestamp(invoice.get('period_start', 0))
        sub.current_period_end = datetime.utcfromtimestamp(invoice.get('period_end', 0))

        # Record invoice
        stripe_inv_id = invoice.get('id')
        if stripe_inv_id and not BillingInvoice.query.filter_by(stripe_invoice_id=stripe_inv_id).first():
            inv = BillingInvoice(
                user_id=sub.user_id,
                stripe_invoice_id=stripe_inv_id,
                amount=invoice.get('amount_paid', 0) / 100,
                currency=invoice.get('currency', 'usd'),
                status='paid',
                period_start=sub.current_period_start,
                period_end=sub.current_period_end,
                paid_at=datetime.utcnow(),
                pdf_url=invoice.get('invoice_pdf'),
            )
            db.session.add(inv)

        db.session.commit()
        current_app.logger.info('Subscription %s marked active after payment', stripe_sub_id)


def _handle_payment_failed(invoice):
    from flask import current_app
    stripe_sub_id = invoice.get('subscription')
    if not stripe_sub_id:
        return
    sub = UserSubscription.query.filter_by(stripe_subscription_id=stripe_sub_id).first()
    if sub:
        sub.status = 'past_due'
        db.session.commit()
        current_app.logger.warning('Subscription %s payment failed — marked past_due', stripe_sub_id)


def _handle_subscription_canceled(subscription_obj):
    from flask import current_app
    stripe_sub_id = subscription_obj.get('id')
    if not stripe_sub_id:
        return
    sub = UserSubscription.query.filter_by(stripe_subscription_id=stripe_sub_id).first()
    if sub:
        sub.status = 'canceled'
        sub.canceled_at = datetime.utcnow()
        db.session.commit()
        current_app.logger.info('Subscription %s canceled via webhook', stripe_sub_id)


def _create_default_plans():
    plans = [
        SubscriptionPlan(name='starter', display_name='Starter', price_monthly=199, price_yearly=1990,
            max_transactions=1000, max_companies=1, max_users=1, has_ai_categorization=True),
        SubscriptionPlan(name='pro', display_name='Pro', price_monthly=499, price_yearly=4990,
            max_transactions=5000, max_companies=3, max_users=3, has_ai_categorization=True,
            has_anomaly_detection=True, has_advanced_reports=True, has_priority_support=True),
        SubscriptionPlan(name='business', display_name='Business', price_monthly=999, price_yearly=9990,
            max_transactions=25000, max_companies=10, max_users=10, has_ai_categorization=True,
            has_anomaly_detection=True, has_cashflow_forecasting=True, has_advanced_reports=True,
            has_api_access=True, has_priority_support=True),
        SubscriptionPlan(name='enterprise', display_name='Enterprise', price_monthly=2499, price_yearly=24990,
            max_transactions=0, max_companies=0, max_users=0, has_ai_categorization=True,
            has_anomaly_detection=True, has_cashflow_forecasting=True, has_advanced_reports=True,
            has_api_access=True, has_priority_support=True, has_dedicated_manager=True),
    ]
    for plan in plans:
        if not SubscriptionPlan.query.filter_by(name=plan.name).first():
            db.session.add(plan)
    db.session.commit()
    return plans[0]


def _create_trial_subscription(user_id, plan_id):
    subscription = UserSubscription(
        user_id=user_id,
        plan_id=plan_id,
        billing_cycle='monthly',
        status='trialing',
        current_period_start=datetime.utcnow(),
        current_period_end=datetime.utcnow() + timedelta(days=14),
    )
    db.session.add(subscription)
    db.session.commit()
    return subscription
