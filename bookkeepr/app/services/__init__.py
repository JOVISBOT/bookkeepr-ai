"""
Services Package
"""
from app.services.qb_auth import QuickBooksAuthService
from app.services.qb_service import QuickBooksService
from app.services.webhook_handler import (
    IntuitWebhookHandler,
    WebhookEventLog,
    WebhookEvent,
    WebhookPayload,
    get_webhook_handler
)
from app.services.ai_categorization import (
    AICategorizationService,
    LearningSystem,
    get_ai_categorization_service,
    get_learning_system,
    CategorizationResult,
    TransactionContext,
    ConfidenceLevel
)

__all__ = [
    'QuickBooksAuthService',
    'QuickBooksService',
    'IntuitWebhookHandler',
    'WebhookEventLog',
    'WebhookEvent',
    'WebhookPayload',
    'get_webhook_handler',
    # AI Categorization (Phase 2)
    'AICategorizationService',
    'LearningSystem',
    'get_ai_categorization_service',
    'get_learning_system',
    'CategorizationResult',
    'TransactionContext',
    'ConfidenceLevel'
]