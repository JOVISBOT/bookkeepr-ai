"""QuickBooks Scheduled Sync - APScheduler for automatic periodic sync"""
import logging
from datetime import datetime, timezone, timedelta

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger

logger = logging.getLogger(__name__)

# Module-level scheduler singleton
_scheduler = None
_SYNC_INTERVAL_MINUTES = 30  # Default: sync every 30 minutes


class SchedulerConfig:
    """Configuration for the QuickBooks sync scheduler"""
    enabled: bool = True
    interval_minutes: int = 30
    company_ids: list[int] | None = None  # None = all connected companies


def _do_sync(app, company_id: int) -> dict:
    """Execute a sync for a single company. Called by APScheduler."""
    from app.models.company import Company
    from app.services.qb_data_sync import QuickBooksDataSync
    from extensions import db

    try:
        with app.app_context():
            company = Company.query.get(company_id)
            if not company or not company.is_connected:
                logger.warning(f"Skipping sync: Company {company_id} not found or not connected")
                return {"status": "skipped", "reason": "not_connected"}

            sync_service = QuickBooksDataSync(company)
            result = sync_service.sync_all()

            company.last_sync_at = datetime.now(timezone.utc)
            company.sync_status = "success"
            db.session.commit()

            logger.info(f"Auto-sync complete for Company {company_id}: {result}")
            return {"status": "success", "company_id": company_id}

    except Exception as e:
        logger.error(f"Auto-sync failed for Company {company_id}: {e}", exc_info=True)
        try:
            with app.app_context():
                from app.models.company import Company
                from extensions import db
                company = Company.query.get(company_id)
                if company:
                    company.sync_status = "error"
                    db.session.commit()
        except Exception:
            pass
        return {"status": "error", "error": str(e)}


def _sync_all_companies(app) -> dict:
    """Sync all connected companies. Called periodically by APScheduler."""
    from app.models.company import Company
    from extensions import db

    try:
        with app.app_context():
            companies = Company.query.filter_by(is_connected=True).all()
            results = []
            for company in companies:
                result = _do_sync(app, company.id)
                results.append(result)
            return {"synced": len(results), "results": results}
    except Exception as e:
        logger.error(f"Auto-sync all companies failed: {e}", exc_info=True)
        return {"status": "error", "error": str(e)}


def init_scheduler(app, config: SchedulerConfig | None = None) -> BackgroundScheduler:
    """Initialize the APScheduler for QuickBooks sync.

    Call this once during app startup (from create_app).
    The scheduler runs in the background and syncs connected
    QuickBooks companies every interval_minutes.

    Usage in app/__init__.py:
        from app.routes.quickbooks.scheduler import init_scheduler
        init_scheduler(app)
    """
    global _scheduler

    if _scheduler is not None:
        logger.info("QuickBooks scheduler already running")
        return _scheduler

    if config is None:
        config = SchedulerConfig()

    if not config.enabled:
        logger.info("QuickBooks scheduler is disabled")
        return None

    interval = config.interval_minutes or _SYNC_INTERVAL_MINUTES

    _scheduler = BackgroundScheduler(daemon=True)
    _scheduler.add_job(
        _sync_all_companies,
        trigger=IntervalTrigger(minutes=interval),
        args=[app],
        id="quickbooks_auto_sync",
        name=f"QuickBooks auto-sync every {interval} minutes",
        replace_existing=True,
        misfire_grace_time=300,  # 5 minutes grace
    )

    _scheduler.start()
    logger.info(f"QuickBooks scheduler started — syncing every {interval} minutes")
    return _scheduler


def stop_scheduler():
    """Stop the scheduler gracefully."""
    global _scheduler
    if _scheduler:
        _scheduler.shutdown(wait=False)
        _scheduler = None
        logger.info("QuickBooks scheduler stopped")
