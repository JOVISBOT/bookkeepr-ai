"""Stripe billing service — lazy import, graceful fallback when keys absent."""
import logging
import os

_logger = logging.getLogger(__name__)


def stripe_enabled() -> bool:
    return bool(os.environ.get('STRIPE_SECRET_KEY') and os.environ.get('STRIPE_PUBLISHABLE_KEY'))


def _stripe():
    """Return stripe module with api_key set. Raises ImportError if not installed."""
    import stripe as _s
    _s.api_key = os.environ.get('STRIPE_SECRET_KEY', '')
    return _s


def get_or_create_customer(user):
    """Return (stripe_customer_id, error). Persists customer_id to UserSubscription."""
    try:
        s = _stripe()
        from app.models.subscription import UserSubscription
        from extensions import db

        sub = UserSubscription.query.filter_by(user_id=user.id).first()
        if sub and sub.stripe_customer_id:
            return sub.stripe_customer_id, None

        customer = s.Customer.create(
            email=user.email,
            name=f"{getattr(user, 'first_name', '')} {getattr(user, 'last_name', '')}".strip() or user.email,
            metadata={'user_id': str(user.id)},
        )
        customer_id = customer['id']

        if sub:
            sub.stripe_customer_id = customer_id
        else:
            sub = UserSubscription(user_id=user.id, stripe_customer_id=customer_id)
            db.session.add(sub)
        db.session.commit()
        return customer_id, None

    except Exception as exc:
        _logger.error('Stripe customer creation failed: %s', exc)
        return None, str(exc)


def create_checkout_session(user, plan_name: str, billing_cycle: str, success_url: str, cancel_url: str):
    """Return (checkout_url, error). Creates a Stripe Checkout Session with 14-day trial."""
    try:
        s = _stripe()
        customer_id, err = get_or_create_customer(user)
        if err:
            return None, err

        price_id = _resolve_price_id(plan_name, billing_cycle)
        if not price_id:
            return None, f'No Stripe price configured for {plan_name}/{billing_cycle}'

        session = s.checkout.Session.create(
            customer=customer_id,
            payment_method_types=['card'],
            line_items=[{'price': price_id, 'quantity': 1}],
            mode='subscription',
            subscription_data={'trial_period_days': 14},
            success_url=success_url,
            cancel_url=cancel_url,
        )
        return session['url'], None

    except Exception as exc:
        _logger.error('Checkout session creation failed: %s', exc)
        return None, str(exc)


def create_billing_portal_session(stripe_customer_id: str, return_url: str):
    """Return (portal_url, error) for Stripe self-serve billing portal."""
    try:
        s = _stripe()
        session = s.billing_portal.Session.create(
            customer=stripe_customer_id,
            return_url=return_url,
        )
        return session['url'], None
    except Exception as exc:
        _logger.error('Billing portal session failed: %s', exc)
        return None, str(exc)


def cancel_subscription(stripe_subscription_id: str, at_period_end: bool = True):
    """Return (subscription, error)."""
    try:
        s = _stripe()
        sub = s.Subscription.modify(stripe_subscription_id, cancel_at_period_end=at_period_end)
        return sub, None
    except Exception as exc:
        _logger.error('Subscription cancellation failed: %s', exc)
        return None, str(exc)


def _resolve_price_id(plan_name: str, billing_cycle: str):
    """DB first, then env var STRIPE_PRICE_<PLAN>_<CYCLE>."""
    try:
        from app.models.subscription import SubscriptionPlan
        plan = SubscriptionPlan.query.filter_by(name=plan_name.lower()).first()
        if plan:
            pid = plan.stripe_price_id_yearly if billing_cycle == 'yearly' else plan.stripe_price_id_monthly
            if pid:
                return pid
    except Exception:
        pass

    key = f'STRIPE_PRICE_{plan_name.upper()}_{billing_cycle.upper()}'
    return os.environ.get(key)
