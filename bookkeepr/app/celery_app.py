"""Celery application factory"""
import os
from celery import Celery
from celery.schedules import crontab


def make_celery(app=None):
    """Create Celery app, optionally bound to a Flask app context"""
    redis_url = os.environ.get('REDIS_URL', 'redis://localhost:6379/0')

    celery = Celery(
        'bookkeepr',
        broker=redis_url,
        backend=redis_url,
        include=[
            'app.tasks.sync',
            'app.tasks.categorization',
            'app.tasks.reports',
        ]
    )

    celery.conf.update(
        task_serializer='json',
        accept_content=['json'],
        result_serializer='json',
        timezone='UTC',
        enable_utc=True,
        task_track_started=True,
        task_acks_late=True,
        worker_prefetch_multiplier=1,
        beat_schedule={
            # Nightly bank sync at 2am UTC
            'nightly-bank-sync': {
                'task': 'app.tasks.sync.sync_all_bank_connections',
                'schedule': crontab(hour=2, minute=0),
            },
            # QBO sync every 4 hours
            'qbo-sync': {
                'task': 'app.tasks.sync.sync_all_quickbooks',
                'schedule': crontab(minute=0, hour='*/4'),
            },
            # Batch AI categorization every 30 minutes
            'auto-categorize': {
                'task': 'app.tasks.categorization.categorize_pending_transactions',
                'schedule': crontab(minute='*/30'),
            },
            # Monthly reports on 1st of each month at 6am UTC
            'monthly-reports': {
                'task': 'app.tasks.reports.generate_monthly_reports',
                'schedule': crontab(day_of_month=1, hour=6, minute=0),
            },
        }
    )

    if app is not None:
        celery.conf.update(app.config)

        class ContextTask(celery.Task):
            def __call__(self, *args, **kwargs):
                with app.app_context():
                    return self.run(*args, **kwargs)

        celery.Task = ContextTask

    return celery


celery = make_celery()
