"""
BookKeepr AI — Email Service

Uses SendGrid when SENDGRID_API_KEY is set.
Falls back to console logging in development so the app works without credentials.
All sends are non-blocking (background thread).
"""
import logging
import os
import threading
from typing import Optional

logger = logging.getLogger(__name__)

# ── Config ────────────────────────────────────────────────────────────────────

_SENDGRID_KEY: Optional[str] = None  # populated by _init()
_MAIL_FROM: str = 'noreply@bookkeepr.ai'
_APP_NAME: str = 'BookKeepr AI'
_APP_URL: str = 'http://localhost:5000'
_initialized = False


def _init() -> None:
    """Read env vars once at first use."""
    global _SENDGRID_KEY, _MAIL_FROM, _APP_NAME, _APP_URL, _initialized
    if _initialized:
        return
    _SENDGRID_KEY = os.environ.get('SENDGRID_API_KEY') or None
    _MAIL_FROM = os.environ.get('MAIL_FROM', 'noreply@bookkeepr.ai')
    _APP_NAME = os.environ.get('APP_NAME', 'BookKeepr AI')
    _APP_URL = os.environ.get('APP_URL', 'http://localhost:5000').rstrip('/')
    _initialized = True


# ── Low-level send ────────────────────────────────────────────────────────────

def _send_via_sendgrid(to: str, subject: str, html: str, text: str) -> bool:
    try:
        from sendgrid import SendGridAPIClient          # lazy import
        from sendgrid.helpers.mail import Mail, From, To, Content, MimeType

        msg = Mail()
        msg.from_email = From(_MAIL_FROM, _APP_NAME)
        msg.to = To(to)
        msg.subject = subject
        msg.content = [
            Content(MimeType.text, text or _strip_html(html)),
            Content(MimeType.html, html),
        ]

        resp = SendGridAPIClient(_SENDGRID_KEY).send(msg)
        logger.info('Email sent to %s via SendGrid (status=%s)', to, resp.status_code)
        return resp.status_code in (200, 202)
    except ImportError:
        logger.error('sendgrid package not installed — add it to requirements.txt')
        return False
    except Exception as exc:
        logger.error('SendGrid send failed for %s: %s', to, exc)
        return False


def _log_fallback(to: str, subject: str, html: str) -> None:
    """Dev fallback: print the email to the server console."""
    divider = '─' * 60
    logger.warning(
        '\n%s\n[EMAIL — set SENDGRID_API_KEY to send for real]\n'
        '  To:      %s\n'
        '  Subject: %s\n%s',
        divider, to, subject, divider,
    )


def _strip_html(html: str) -> str:
    """Minimal HTML → plain text (remove tags, collapse whitespace)."""
    import re
    text = re.sub(r'<[^>]+>', ' ', html)
    text = re.sub(r'\s+', ' ', text)
    return text.strip()


def send_email(to: str, subject: str, html: str, text: str = '') -> None:
    """
    Send an email asynchronously in a background daemon thread.
    Never raises — errors are logged.
    """
    _init()

    def _worker():
        if _SENDGRID_KEY:
            _send_via_sendgrid(to, subject, html, text)
        else:
            _log_fallback(to, subject, html)

    threading.Thread(target=_worker, daemon=True, name=f'email-{to}').start()


def send_email_sync(to: str, subject: str, html: str, text: str = '') -> bool:
    """Synchronous variant — for use in tests or background jobs."""
    _init()
    if _SENDGRID_KEY:
        return _send_via_sendgrid(to, subject, html, text)
    _log_fallback(to, subject, html)
    return True   # fallback counts as success in tests


# ── Template rendering ────────────────────────────────────────────────────────

def _render(template_name: str, **ctx) -> str:
    """Render an email Jinja2 template. Must be called within Flask app context."""
    from flask import render_template
    return render_template(f'email/{template_name}', **ctx,
                           app_name=_APP_NAME, app_url=_APP_URL)


# ── Public send helpers ───────────────────────────────────────────────────────

def send_welcome(user) -> None:
    """Welcome email sent after registration."""
    _init()
    html = _render('welcome.html',
                   first_name=user.first_name or user.email.split('@')[0],
                   dashboard_url=f'{_APP_URL}/dashboard/')
    send_email(
        to=user.email,
        subject=f'Welcome to {_APP_NAME} — your trial has started',
        html=html,
    )


def send_password_reset(user, reset_url: str) -> None:
    """Password reset link email."""
    _init()
    html = _render('password_reset.html',
                   first_name=user.first_name or user.email.split('@')[0],
                   reset_url=reset_url)
    send_email(
        to=user.email,
        subject=f'{_APP_NAME} — reset your password',
        html=html,
    )


def send_review_alert(user, company_name: str, pending_count: int, review_url: str) -> None:
    """Notify operator that transactions are waiting in the review queue."""
    _init()
    html = _render('review_alert.html',
                   first_name=user.first_name or user.email.split('@')[0],
                   company_name=company_name,
                   pending_count=pending_count,
                   review_url=review_url)
    send_email(
        to=user.email,
        subject=f'{company_name} — {pending_count} transaction{"s" if pending_count != 1 else ""} need review',
        html=html,
    )


def send_monthly_summary(user, company_name: str, summary: dict) -> None:
    """
    Monthly financial summary.
    summary keys: period_label, revenue, expenses, net_income,
                  top_categories (list of {name, amount}), transaction_count,
                  report_url
    """
    _init()
    html = _render('monthly_summary.html',
                   first_name=user.first_name or user.email.split('@')[0],
                   company_name=company_name,
                   **summary)
    send_email(
        to=user.email,
        subject=f'{company_name} — {summary.get("period_label", "Monthly")} summary',
        html=html,
    )
