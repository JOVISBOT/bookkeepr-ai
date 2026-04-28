"""Pricing Page Routes"""
from flask import Blueprint, render_template
from app.services.stripe_service import stripe_enabled

bp = Blueprint('pricing', __name__)


@bp.route('/pricing')
def index():
    """Pricing page with 4 tiers"""
    plans = [
        {
            'slug': 'starter',
            'name': 'Starter',
            'price': 199,
            'description': 'Perfect for freelancers and solo bookkeepers',
            'features': [
                'Up to 1,000 transactions/month',
                '1 company',
                'Basic AI categorization',
                'Email support',
                'Standard reports',
            ],
            'not_included': [
                'Anomaly detection',
                'Cash flow forecasting',
                'API access',
                'Priority support',
            ],
            'cta': 'Get Started',
            'popular': False,
        },
        {
            'slug': 'pro',
            'name': 'Pro',
            'price': 499,
            'description': 'For growing firms with multiple clients',
            'features': [
                'Up to 5,000 transactions/month',
                '3 companies',
                'Advanced AI categorization',
                'Human-in-the-loop review',
                'Anomaly detection alerts',
                'Priority email support',
            ],
            'not_included': [
                'Cash flow forecasting',
                'API access',
                'Dedicated account manager',
            ],
            'cta': 'Start Pro Trial',
            'popular': True,
        },
        {
            'slug': 'business',
            'name': 'Business',
            'price': 999,
            'description': 'For established practices needing automation',
            'features': [
                'Up to 25,000 transactions/month',
                '10 companies',
                'Premium AI with learning feedback',
                'Cash flow forecasting',
                'Advanced anomaly detection',
                'Custom categorization rules',
                'API access',
                'Priority chat support',
            ],
            'not_included': [
                'Dedicated account manager',
            ],
            'cta': 'Start Business Trial',
            'popular': False,
        },
        {
            'slug': 'enterprise',
            'name': 'Enterprise',
            'price': 2499,
            'description': 'White-glove service for large firms',
            'features': [
                'Unlimited transactions',
                'Unlimited companies',
                'Custom AI model training',
                'Full feature access',
                'SSO & advanced security',
                'Custom integrations',
                'Dedicated account manager',
                '24/7 phone support',
                'SLA guarantee',
            ],
            'not_included': [],
            'cta': 'Contact Sales',
            'popular': False,
        },
    ]
    
    comparison_features = [
        {'name': 'Monthly Transactions', 'starter': '1,000', 'pro': '5,000', 'business': '25,000', 'enterprise': 'Unlimited'},
        {'name': 'Companies', 'starter': '1', 'pro': '3', 'business': '10', 'enterprise': 'Unlimited'},
        {'name': 'AI Categorization', 'starter': 'Basic', 'pro': 'Advanced', 'business': 'Premium', 'enterprise': 'Custom'},
        {'name': 'Human Review Queue', 'starter': False, 'pro': True, 'business': True, 'enterprise': True},
        {'name': 'Anomaly Detection', 'starter': False, 'pro': True, 'business': 'Advanced', 'enterprise': 'Advanced'},
        {'name': 'Cash Flow Forecasting', 'starter': False, 'pro': False, 'business': True, 'enterprise': True},
        {'name': 'Custom Rules', 'starter': False, 'pro': False, 'business': True, 'enterprise': True},
        {'name': 'API Access', 'starter': False, 'pro': False, 'business': True, 'enterprise': True},
        {'name': 'Support', 'starter': 'Email', 'pro': 'Priority Email', 'business': 'Priority Chat', 'enterprise': '24/7 Phone'},
        {'name': 'Account Manager', 'starter': False, 'pro': False, 'business': False, 'enterprise': True},
    ]
    
    return render_template('pricing.html', plans=plans, comparison=comparison_features,
                           stripe_enabled=stripe_enabled())
