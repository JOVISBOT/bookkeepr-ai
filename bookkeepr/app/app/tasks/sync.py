"""Background sync tasks — bank feeds and QuickBooks"""
import logging
from datetime import datetime, timedelta

from celery_app import celery

logger = logging.getLogger(__name__)


@celery.task(bind=True, max_retries=3, default_retry_delay=300)
def sync_all_bank_connections(self):
    """Nightly task: sync transactions for every active Plaid connection"""
    from extensions import db
    from app.models.bank_connection import BankConnection
    from app.services.plaid_service import PlaidService

    connections = BankConnection.query.filter_by(status='active').all()
    logger.info(f'Starting nightly bank sync for {len(connections)} connections')

    results = {'synced': 0, 'failed': 0, 'new_transactions': 0}

    for conn in connections:
        try:
            sync_bank_connection.delay(conn.id)
            results['synced'] += 1
        except Exception as e:
            logger.error(f'Failed to queue sync for connection {conn.id}: {e}')
            results['failed'] += 1

    logger.info(f'Nightly bank sync queued: {results}')
    return results


@celery.task(bind=True, max_retries=3, default_retry_delay=60)
def sync_bank_connection(self, connection_id):
    """Sync a single Plaid bank connection"""
    from extensions import db
    from app.models.bank_connection import BankConnection, BankTransaction
    from app.services.plaid_service import PlaidService

    conn = BankConnection.query.get(connection_id)
    if not conn:
        logger.warning(f'Bank connection {connection_id} not found')
        return

    try:
        plaid = PlaidService()
        start_date = (conn.last_sync_at or datetime.utcnow() - timedelta(days=30)).date()
        end_date = datetime.utcnow().date()

        transactions_data = plaid.get_transactions(
            conn.plaid_access_token, str(start_date), str(end_date)
        )

        new_count = 0
        for txn in transactions_data.get('transactions', []):
            existing = BankTransaction.query.filter_by(
                plaid_transaction_id=txn['transaction_id']
            ).first()
            if not existing:
                bt = BankTransaction(
                    bank_connection_id=conn.id,
                    tenant_id=conn.tenant_id,
                    plaid_transaction_id=txn['transaction_id'],
                    date=datetime.strptime(txn['date'], '%Y-%m-%d').date(),
                    amount=txn['amount'],
                    description=txn.get('name', ''),
                    merchant_name=txn.get('merchant_name'),
                    category=txn.get('category', [None])[0],
                    pending=txn.get('pending', False),
                )
                db.session.add(bt)
                new_count += 1

        conn.last_sync_at = datetime.utcnow()
        conn.status = 'active'
        db.session.commit()

        logger.info(f'Synced connection {connection_id}: {new_count} new transactions')
        return {'connection_id': connection_id, 'new_transactions': new_count}

    except Exception as e:
        logger.error(f'Bank sync failed for connection {connection_id}: {e}')
        conn.status = 'error'
        db.session.commit()
        raise self.retry(exc=e)


@celery.task(bind=True, max_retries=3, default_retry_delay=300)
def sync_all_quickbooks(self):
    """Sync QBO data for all active company connections"""
    from app.models.company import Company

    companies = Company.query.filter_by(is_active=True).all()
    logger.info(f'Starting QBO sync for {len(companies)} companies')

    for company in companies:
        sync_quickbooks_company.delay(company.id)

    return {'queued': len(companies)}


@celery.task(bind=True, max_retries=3, default_retry_delay=120)
def sync_quickbooks_company(self, company_id):
    """Sync a single QBO company's transactions and accounts"""
    from extensions import db
    from app.models.company import Company
    from app.services.qb_service import QBService

    company = Company.query.get(company_id)
    if not company:
        return

    try:
        svc = QBService(company)
        result = svc.sync_transactions()
        company.last_synced_at = datetime.utcnow()
        db.session.commit()
        logger.info(f'QBO sync complete for company {company_id}: {result}')
        return result
    except Exception as e:
        logger.error(f'QBO sync failed for company {company_id}: {e}')
        raise self.retry(exc=e)
