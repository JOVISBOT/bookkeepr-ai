"""Background report generation and email delivery tasks"""
import logging
from datetime import datetime, timedelta

from celery_app import celery

logger = logging.getLogger(__name__)


@celery.task
def generate_monthly_reports():
    """Generate and email monthly reports for all active tenants"""
    from app.models.company import Company

    last_month = datetime.utcnow().replace(day=1) - timedelta(days=1)
    period_start = last_month.replace(day=1)
    period_end = last_month

    companies = Company.query.filter_by(is_active=True).all()
    logger.info(f'Generating monthly reports for {len(companies)} companies ({period_start.strftime("%B %Y")})')

    for company in companies:
        generate_company_report.delay(company.id, period_start.isoformat(), period_end.isoformat())

    return {'queued': len(companies), 'period': period_start.strftime('%B %Y')}


@celery.task(bind=True, max_retries=2, default_retry_delay=120)
def generate_company_report(self, company_id, period_start_str, period_end_str):
    """Generate PDF report for a single company and email it"""
    from extensions import db
    from app.models.company import Company
    from app.models.subscription import UserSubscription
    from app.services.report_pdf import ReportPDFService

    company = Company.query.get(company_id)
    if not company:
        return

    try:
        period_start = datetime.fromisoformat(period_start_str)
        period_end = datetime.fromisoformat(period_end_str)

        pdf_service = ReportPDFService()
        pdf_path = pdf_service.generate_pl_report(company, period_start, period_end)

        if pdf_path and company.owner and company.owner.email:
            send_report_email.delay(
                to_email=company.owner.email,
                company_name=company.company_name,
                period=period_start.strftime('%B %Y'),
                pdf_path=pdf_path,
            )

        logger.info(f'Report generated for company {company_id}')
        return {'company_id': company_id, 'pdf_path': pdf_path}

    except Exception as e:
        logger.error(f'Report generation failed for company {company_id}: {e}')
        raise self.retry(exc=e)


@celery.task
def send_report_email(to_email, company_name, period, pdf_path):
    """Send a report PDF via email using SendGrid or SMTP"""
    import os
    import smtplib
    from email.mime.multipart import MIMEMultipart
    from email.mime.base import MIMEBase
    from email.mime.text import MIMEText
    from email import encoders

    smtp_host = os.environ.get('SMTP_HOST')
    smtp_port = int(os.environ.get('SMTP_PORT', 587))
    smtp_user = os.environ.get('SMTP_USER')
    smtp_pass = os.environ.get('SMTP_PASS')
    from_email = os.environ.get('FROM_EMAIL', smtp_user)

    if not all([smtp_host, smtp_user, smtp_pass]):
        logger.warning(f'SMTP not configured — skipping report email to {to_email}')
        return

    try:
        msg = MIMEMultipart()
        msg['From'] = from_email
        msg['To'] = to_email
        msg['Subject'] = f'Your {period} Financial Report — {company_name}'

        body = (
            f'Hi,\n\nPlease find your {period} financial report for {company_name} attached.\n\n'
            f'Log in to your Bookkeepr dashboard to view full details and download additional reports.\n\n'
            f'— The Bookkeepr AI Team'
        )
        msg.attach(MIMEText(body, 'plain'))

        if pdf_path:
            with open(pdf_path, 'rb') as f:
                part = MIMEBase('application', 'octet-stream')
                part.set_payload(f.read())
                encoders.encode_base64(part)
                part.add_header('Content-Disposition', f'attachment; filename="{company_name}_{period}_Report.pdf"')
                msg.attach(part)

        with smtplib.SMTP(smtp_host, smtp_port) as server:
            server.starttls()
            server.login(smtp_user, smtp_pass)
            server.send_message(msg)

        logger.info(f'Report emailed to {to_email}')

    except Exception as e:
        logger.error(f'Failed to send report email to {to_email}: {e}')
