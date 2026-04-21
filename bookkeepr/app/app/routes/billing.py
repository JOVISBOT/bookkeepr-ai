"""Billing and subscription routes"""
from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
from app.extensions import db
from app.models.subscription import Subscription
from app.services.stripe_service import StripeService
import os

billing_bp = Blueprint('billing', __name__, url_prefix='/api/v1/billing')


@billing_bp.route('/plans', methods=['GET'])
def get_plans():
    """Get available pricing plans"""
    plans = StripeService.get_all_plans()
    return jsonify({
        'success': True,
        'plans': plans
    })


@billing_bp.route('/subscription', methods=['GET'])
@login_required
def get_subscription():
    """Get current user's subscription"""
    subscription = Subscription.query.filter_by(user_id=current_user.id).first()
    
    if not subscription:
        return jsonify({
            'success': True,
            'subscription': None,
            'has_active_subscription': False
        })
    
    return jsonify({
        'success': True,
        'subscription': subscription.to_dict(),
        'has_active_subscription': subscription.is_active()
    })


@billing_bp.route('/create-checkout', methods=['POST'])
@login_required
def create_checkout():
    """Create Stripe checkout session"""
    data = request.get_json()
    plan_type = data.get('plan_type', 'standard')
    
    # Get or create subscription record
    subscription = Subscription.query.filter_by(user_id=current_user.id).first()
    
    if not subscription:
        # Create Stripe customer
        customer = StripeService.create_customer(current_user)
        if not customer:
            return jsonify({
                'success': False,
                'message': 'Failed to create customer'
            }), 500
        
        subscription = Subscription(
            user_id=current_user.id,
            stripe_customer_id=customer.id,
            plan_type=plan_type
        )
        db.session.add(subscription)
        db.session.commit()
    
    # Create checkout session
    frontend_url = os.environ.get('FRONTEND_URL', 'http://localhost:3000')
    success_url = f"{frontend_url}/billing/success?session_id={{CHECKOUT_SESSION_ID}}"
    cancel_url = f"{frontend_url}/billing/cancel"
    
    session = StripeService.create_checkout_session(
        subscription.stripe_customer_id,
        plan_type,
        success_url,
        cancel_url
    )
    
    if not session:
        return jsonify({
            'success': False,
            'message': 'Failed to create checkout session'
        }), 500
    
    return jsonify({
        'success': True,
        'checkout_url': session.url,
        'session_id': session.id
    })


@billing_bp.route('/cancel', methods=['POST'])
@login_required
def cancel_subscription():
    """Cancel subscription at period end"""
    subscription = Subscription.query.filter_by(user_id=current_user.id).first()
    
    if not subscription or not subscription.stripe_subscription_id:
        return jsonify({
            'success': False,
            'message': 'No active subscription found'
        }), 404
    
    result = StripeService.cancel_subscription(subscription.stripe_subscription_id)
    
    if result:
        subscription.status = 'canceled'
        db.session.commit()
        return jsonify({
            'success': True,
            'message': 'Subscription will be canceled at period end'
        })
    
    return jsonify({
        'success': False,
        'message': 'Failed to cancel subscription'
    }), 500


@billing_bp.route('/update', methods=['POST'])
@login_required
def update_subscription():
    """Update subscription plan"""
    data = request.get_json()
    new_plan = data.get('plan_type')
    
    if not new_plan:
        return jsonify({
            'success': False,
            'message': 'Plan type required'
        }), 400
    
    subscription = Subscription.query.filter_by(user_id=current_user.id).first()
    
    if not subscription or not subscription.stripe_subscription_id:
        return jsonify({
            'success': False,
            'message': 'No active subscription found'
        }), 404
    
    price_id = os.environ.get(f'STRIPE_PRICE_{new_plan.upper()}')
    result = StripeService.update_subscription(
        subscription.stripe_subscription_id,
        price_id
    )
    
    if result:
        subscription.plan_type = new_plan
        db.session.commit()
        return jsonify({
            'success': True,
            'message': f'Subscription updated to {new_plan}'
        })
    
    return jsonify({
        'success': False,
        'message': 'Failed to update subscription'
    }), 500


@billing_bp.route('/webhook', methods=['POST'])
def webhook():
    """Handle Stripe webhooks"""
    payload = request.get_data()
    sig_header = request.headers.get('Stripe-Signature')
    
    event = StripeService.construct_event(payload, sig_header)
    
    if not event:
        return jsonify({'success': False}), 400
    
    # Handle the event
    if event['type'] == 'checkout.session.completed':
        session = event['data']['object']
        
        # Update subscription
        customer_id = session.get('customer')
        subscription_id = session.get('subscription')
        
        subscription = Subscription.query.filter_by(
            stripe_customer_id=customer_id
        ).first()
        
        if subscription:
            subscription.stripe_subscription_id = subscription_id
            subscription.status = 'active'
            db.session.commit()
    
    elif event['type'] == 'invoice.payment_failed':
        subscription_id = event['data']['object'].get('subscription')
        
        subscription = Subscription.query.filter_by(
            stripe_subscription_id=subscription_id
        ).first()
        
        if subscription:
            subscription.status = 'past_due'
            db.session.commit()
    
    return jsonify({'success': True})
