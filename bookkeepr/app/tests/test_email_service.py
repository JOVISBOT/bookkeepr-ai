"""Tests for email_service — no real sends, verifies fallback and rendering."""
import os
import pytest


class TestEmailServiceInit:
    def test_imports_without_sendgrid_installed(self):
        """Service loads even if sendgrid package is absent."""
        from app.services import email_service
        assert callable(email_service.send_email)
        assert callable(email_service.send_email_sync)

    def test_no_api_key_returns_true(self, app):
        """send_email_sync returns True (console fallback) when no API key."""
        with app.app_context():
            os.environ.pop('SENDGRID_API_KEY', None)
            import app.services.email_service as svc
            # Reset init so it re-reads env
            svc._initialized = False
            result = svc.send_email_sync(
                to='test@example.com',
                subject='Test',
                html='<p>Hello</p>',
            )
            assert result is True

    def test_strip_html(self):
        from app.services.email_service import _strip_html
        assert 'Hello World' in _strip_html('<h1>Hello</h1> <p>World</p>')


class TestEmailTemplates:
    def test_welcome_renders(self, app):
        with app.app_context():
            from flask import render_template
            html = render_template(
                'email/welcome.html',
                first_name='Jane',
                dashboard_url='http://localhost:5000/dashboard/',
                app_name='BookKeepr AI',
                app_url='http://localhost:5000',
            )
            assert 'Jane' in html
            assert 'dashboard' in html.lower()
            assert 'BookKeepr' in html

    def test_password_reset_renders(self, app):
        with app.app_context():
            from flask import render_template
            html = render_template(
                'email/password_reset.html',
                first_name='Jane',
                reset_url='http://localhost:5000/auth/reset-password/abc123',
                app_name='BookKeepr AI',
                app_url='http://localhost:5000',
            )
            assert 'Jane' in html
            assert 'abc123' in html
            assert '1 hour' in html

    def test_review_alert_renders(self, app):
        with app.app_context():
            from flask import render_template
            html = render_template(
                'email/review_alert.html',
                first_name='Jane',
                company_name='Acme Corp',
                pending_count=7,
                review_url='http://localhost:5000/review',
                app_name='BookKeepr AI',
                app_url='http://localhost:5000',
            )
            assert '7' in html
            assert 'Acme Corp' in html

    def test_monthly_summary_renders(self, app):
        with app.app_context():
            from flask import render_template
            html = render_template(
                'email/monthly_summary.html',
                first_name='Jane',
                company_name='Acme Corp',
                period_label='April 2026',
                revenue=50000,
                expenses=32000,
                net_income=18000,
                transaction_count=142,
                top_categories=[
                    {'name': 'Software & Technology', 'amount': 4500},
                    {'name': 'Payroll', 'amount': 20000},
                ],
                report_url='http://localhost:5000/dashboard/reports',
                app_name='BookKeepr AI',
                app_url='http://localhost:5000',
            )
            assert 'April 2026' in html
            assert 'Acme Corp' in html
            assert '50,000' in html
            assert 'Software' in html


class TestSendHelpers:
    def test_send_welcome_does_not_raise(self, app, test_user):
        """send_welcome fires without exception even with no API key."""
        with app.app_context():
            import app.services.email_service as svc
            svc._initialized = False
            os.environ.pop('SENDGRID_API_KEY', None)
            # Should not raise
            svc.send_welcome(test_user)

    def test_send_password_reset_does_not_raise(self, app, test_user):
        with app.app_context():
            import app.services.email_service as svc
            svc._initialized = False
            os.environ.pop('SENDGRID_API_KEY', None)
            svc.send_password_reset(test_user, 'http://localhost/reset/abc')

    def test_send_review_alert_does_not_raise(self, app, test_user):
        with app.app_context():
            import app.services.email_service as svc
            svc._initialized = False
            os.environ.pop('SENDGRID_API_KEY', None)
            svc.send_review_alert(test_user, 'Acme Corp', 5, 'http://localhost/review')

    def test_send_monthly_summary_does_not_raise(self, app, test_user):
        with app.app_context():
            import app.services.email_service as svc
            svc._initialized = False
            os.environ.pop('SENDGRID_API_KEY', None)
            svc.send_monthly_summary(test_user, 'Acme Corp', {
                'period_label': 'April 2026',
                'revenue': 10000,
                'expenses': 6000,
                'net_income': 4000,
                'transaction_count': 50,
                'top_categories': [],
                'report_url': 'http://localhost/reports',
            })
