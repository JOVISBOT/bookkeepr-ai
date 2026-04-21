"""Stripe billing service"""
import os
from datetime import datetime
import stripe
from flask import current_app

# Set Stripe API key
stripe.api_key = os.environ.get('STRIPE_SECRET_KEY')

# Price IDs for different plans
PRICE_IDS = {
    'standard': os.environ.get('STRIPE_PRICE_STANDARD', 'price_standard'),
    'silver': os.environ.get('STRIPE_PRICE_SILVER', 'price_silver'),
    'gold': os.environ.get('STRIPE_PRICE_GOLD', 'price_gold')
}

PLAN_DETAILS = {
    'standard': {
        'name': 'Standard',
        'price': 199,
        'features': ['QBO Integration', 'AI Categorization', 'Dashboard', 'Email Support']
    },
    'silver': {
        'name': 'Silver',
        'price': 299,
        'features': ['Everything in Standard', 'QBD Integration', 'Bank Reconciliation', 'Priority Support']
    },
    'gold': {
        'name': 'Gold',
        'price': 399,
        'features': ['Everything in Silver', 'Multi-Company', 'API Access', 'Dedicated Support']
    }
}


class StripeService:
    """Handle all Stripe operations"""
    
    @staticmethod
    def create_customer(user):
        """Create a Stripe customer for user"""
        try:
            customer = stripe.Customer.create(
                email=user.email,
                name=user.name if hasattr(user, 'name') else user.email,
                metadata={
                    'user_id': str(user.id)
                }
            )
            return customer
        except stripe.error.StripeError as e:
            current_app.logger.error(f"Stripe customer creation failed: {e}")
            return None
    
    @staticmethod
    def create_checkout_session(customer_id, plan_type, success_url, cancel_url):
        """Create Stripe checkout session for subscription"""
        try:
            price_id = PRICE_IDS.get(plan_type)
            if not price_id:
                return None
            
            session = stripe.checkout.Session.create(
                customer=customer_id,
                payment_method_types=['card'],
                line_items=[{
                    'price': price_id,
                    'quantity': 1,
                }],
                mode='subscription',
                success_url=success_url,
                cancel_url=cancel_url,
            )
            return session
        except stripe.error.StripeError as e:
            current_app.logger.error(f"Checkout session creation failed: {e}")
            return None
    
    @staticmethod
    def cancel_subscription(stripe_subscription_id):
        """Cancel subscription at period end"""
        try:
            subscription = stripe.Subscription.modify(
                stripe_subscription_id,
                cancel_at_period_end=True
            )
            return subscription
        except stripe.error.StripeError as e:
            current_app.logger.error(f"Subscription cancellation failed: {e}")
            return None
    
    @staticmethod
    def update_subscription(stripe_subscription_id, new_price_id):
        """Update subscription to new plan"""
        try:
            subscription = stripe.Subscription.retrieve(stripe_subscription_id)
            
            # Update the subscription item
            subscription_item_id = subscription['items']['data'][0]['id']
            
            updated = stripe.Subscription.modify(
                stripe_subscription_id,
                items=[{
                    'id': subscription_item_id,
                    'price': new_price_id,
                }],
                proration_behavior='create_prorations'
            )
            return updated
        except stripe.error.StripeError as e:
            current_app.logger.error(f"Subscription update failed: {e}")
            return None
    
    @staticmethod
    def construct_event(payload, sig_secret):
        """Verify webhook signature and construct event"""
        try:
            event = stripe.Webhook.construct_event(
                payload, sig_secret, os.environ.get('STRIPE_WEBHOOK_SECRET', '')
            )
            return event
        except ValueError as e:
            # Invalid payload
            current_app.logger.error(f"Invalid webhook payload: {e}")
            return None
        except stripe.error.SignatureVerificationError as e:
            # Invalid signature
            current_app.logger.error(f"Invalid webhook signature: {e}")
            return None
    
    @staticmethod
    def get_plan_details(plan_type):
        """Get plan details"""
        return PLAN_DETAILS.get(plan_type, PLAN_DETAILS['standard'])
    
    @staticmethod
    def get_all_plans():
        """Get all available plans"""
        return PLAN_DETAILS
