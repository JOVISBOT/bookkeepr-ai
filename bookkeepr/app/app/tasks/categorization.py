"""Background AI categorization tasks"""
import logging

from celery_app import celery

logger = logging.getLogger(__name__)


@celery.task(bind=True, max_retries=2, default_retry_delay=60)
def categorize_pending_transactions(self):
    """Batch-categorize all uncategorized transactions across all tenants"""
    from app.models.transaction import Transaction

    pending = Transaction.query.filter_by(status='uncategorized').limit(100).all()
    if not pending:
        return {'categorized': 0}

    logger.info(f'Batch categorizing {len(pending)} transactions')

    for txn in pending:
        categorize_transaction.delay(txn.id)

    return {'queued': len(pending)}


@celery.task(bind=True, max_retries=3, default_retry_delay=30)
def categorize_transaction(self, transaction_id):
    """Categorize a single transaction using the AI engine"""
    from extensions import db
    from app.models.transaction import Transaction
    from app.services.ai_categorization import AICategorizer

    txn = Transaction.query.get(transaction_id)
    if not txn:
        return

    try:
        categorizer = AICategorizer()
        result = categorizer.categorize(txn)

        txn.category = result.get('category')
        txn.confidence_score = result.get('confidence', 0)
        txn.ai_suggested_category = result.get('category')

        if result.get('confidence', 0) >= 0.8:
            txn.status = 'categorized'
        elif result.get('confidence', 0) >= 0.5:
            txn.status = 'needs_review'
        else:
            txn.status = 'needs_review'

        db.session.commit()
        return {'transaction_id': transaction_id, 'category': txn.category, 'confidence': txn.confidence_score}

    except Exception as e:
        logger.error(f'Categorization failed for transaction {transaction_id}: {e}')
        raise self.retry(exc=e)


@celery.task
def learn_from_correction(transaction_id, corrected_category):
    """Record a user correction to improve future AI accuracy"""
    from extensions import db
    from app.models.transaction import Transaction
    from app.models.category_rule import CategoryRule

    txn = Transaction.query.get(transaction_id)
    if not txn or not txn.description:
        return

    # Create a keyword rule from the correction
    existing = CategoryRule.query.filter_by(
        company_id=txn.company_id,
        category=corrected_category,
        rule_type='vendor',
        value=txn.description[:100]
    ).first()

    if not existing:
        rule = CategoryRule(
            company_id=txn.company_id,
            category=corrected_category,
            rule_type='vendor',
            value=txn.description[:100],
            priority=10,
        )
        db.session.add(rule)
        db.session.commit()
        logger.info(f'Learned rule: "{txn.description[:50]}" → {corrected_category}')
