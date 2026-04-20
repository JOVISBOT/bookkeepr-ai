"""
Background sync tasks for QuickBooks data
"""
from celery import shared_task
from flask import current_app

from ..extensions import db
from ..models import Company
from ..services.qb_service import QuickBooksService


@shared_task(bind=True, max_retries=3)
def sync_company_transactions(self, company_id):
    """
    Sync transactions for a single company.
    
    Args:
        company_id: Company ID to sync
    """
    with current_app.app_context():
        company = Company.query.get(company_id)
        
        if not company:
            return {'error': 'Company not found'}
        
        if not company.is_active:
            return {'error': 'Company not active'}
        
        try:
            qb_service = QuickBooksService(company=company)
            result = qb_service.import_transactions()
            
            return {
                'company_id': company_id,
                'company_name': company.company_name,
                'result': result
            }
            
        except Exception as exc:
            # Retry on failure
            self.retry(countdown=60, exc=exc)
            return {'error': str(exc)}


@shared_task
def sync_all_companies():
    """
    Sync transactions for all active companies.
    Run this hourly via Celery beat.
    """
    with current_app.app_context():
        companies = Company.query.filter_by(is_active=True).all()
        results = []
        
        for company in companies:
            # Queue individual sync tasks
            result = sync_company_transactions.delay(company.id)
            results.append({
                'company_id': company.id,
                'company_name': company.company_name,
                'task_id': result.id
            })
        
        return {
            'total_companies': len(companies),
            'tasks_queued': results
        }


@shared_task
def refresh_all_tokens():
    """
    Refresh OAuth tokens for all companies before expiration.
    Run this every 30 minutes via Celery beat.
    """
    with current_app.app_context():
        # Get companies with tokens expiring soon (within 1 hour)
        from datetime import datetime, timedelta
        
        companies = Company.query.filter(
            Company.is_active == True,
            Company.token_expires_at <= datetime.utcnow() + timedelta(hours=1)
        ).all()
        
        refreshed = 0
        failed = 0
        
        for company in companies:
            try:
                qb_service = QuickBooksService(company=company)
                if qb_service.refresh_access_token():
                    refreshed += 1
                else:
                    failed += 1
            except Exception as e:
                current_app.logger.error(f"Token refresh failed for {company.id}: {e}")
                failed += 1
        
        return {
            'total': len(companies),
            'refreshed': refreshed,
            'failed': failed
        }
