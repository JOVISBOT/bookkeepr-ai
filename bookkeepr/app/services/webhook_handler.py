"""
Intuit QuickBooks Webhook Handler

Handles webhook events from Intuit for real-time data updates.

Webhook Events Supported:
- Account changes (create, update, delete)
- Transaction changes (Purchase, Deposit, JournalEntry, Payment, etc.)
- Entity changes (Customer, Vendor, Item, etc.)

Reference: https://developer.intuit.com/app/developer/qbo/docs/develop/webhooks
"""
import hmac
import hashlib
import base64
import json
import logging
from datetime import datetime
from typing import Dict, List, Optional, Callable
from dataclasses import dataclass
from enum import Enum

from app import db
from app.models.company import Company
from app.services.qb_data_sync import QuickBooksDataSync

logger = logging.getLogger(__name__)


class WebhookEventType(Enum):
    """Intuit webhook event types"""
    CREATE = "Create"
    UPDATE = "Update"
    DELETE = "Delete"


class WebhookEntityType(Enum):
    """Intuit webhook entity types we care about"""
    ACCOUNT = "Account"
    PURCHASE = "Purchase"
    DEPOSIT = "Deposit"
    JOURNAL_ENTRY = "JournalEntry"
    PAYMENT = "Payment"
    INVOICE = "Invoice"
    BILL = "Bill"
    CUSTOMER = "Customer"
    VENDOR = "Vendor"
    ITEM = "Item"
    TRANSFER = "Transfer"
    CREDIT_CARD_CHARGE = "CreditCardCharge"
    CREDIT_CARD_CREDIT = "CreditCardCredit"


@dataclass
class WebhookEvent:
    """Represents a single webhook event"""
    entity_id: str
    entity_type: str
    operation: str
    realm_id: str  # Company ID in QBO
    last_updated: Optional[datetime] = None
    
    def __post_init__(self):
        """Normalize entity type for internal use"""
        # Map Intuit entity types to our internal types
        type_map = {
            'JournalEntry': 'JournalEntry',
            'CreditCardCharge': 'Purchase',
            'CreditCardCredit': 'Deposit',
        }
        self.entity_type = type_map.get(self.entity_type, self.entity_type)


@dataclass
class WebhookPayload:
    """Represents the full webhook payload"""
    events: List[WebhookEvent]
    realm_ids: List[str]
    notification_id: Optional[str] = None


class IntuitWebhookHandler:
    """
    Handler for Intuit webhook events
    
    Responsibilities:
    1. Verify webhook signature (security)
    2. Parse and validate webhook payload
    3. Route events to appropriate handlers
    4. Trigger syncs for changed entities
    5. Log events for debugging
    """
    
    def __init__(self, webhook_secret: str, webhook_token: Optional[str] = None):
        """
        Initialize webhook handler
        
        Args:
            webhook_secret: Shared secret from Intuit Developer Portal
            webhook_token: Optional verifier token for additional validation
        """
        self.webhook_secret = webhook_secret
        self.webhook_token = webhook_token
        self.event_handlers: Dict[str, Callable] = {}
        
        # Register default handlers
        self._register_default_handlers()
    
    def _register_default_handlers(self):
        """Register default event handlers"""
        # Account handlers
        self.event_handlers['Account'] = self._handle_account_event
        
        # Transaction handlers
        self.event_handlers['Purchase'] = self._handle_transaction_event
        self.event_handlers['Deposit'] = self._handle_transaction_event
        self.event_handlers['JournalEntry'] = self._handle_transaction_event
        self.event_handlers['Payment'] = self._handle_transaction_event
        self.event_handlers['Invoice'] = self._handle_transaction_event
        self.event_handlers['Bill'] = self._handle_transaction_event
        self.event_handlers['CreditCardCharge'] = self._handle_transaction_event
        self.event_handlers['CreditCardCredit'] = self._handle_transaction_event
        self.event_handlers['Transfer'] = self._handle_transaction_event
        
        # Entity handlers
        self.event_handlers['Customer'] = self._handle_entity_event
        self.event_handlers['Vendor'] = self._handle_entity_event
        self.event_handlers['Item'] = self._handle_entity_event
    
    def verify_signature(self, payload: bytes, signature: str) -> bool:
        """
        Verify the webhook signature from Intuit
        
        Intuit sends the signature in the 'intuit-signature' header.
        The signature is a base64-encoded HMAC-SHA256 hash of the payload.
        
        Args:
            payload: Raw request body bytes
            signature: Signature from intuit-signature header
            
        Returns:
            True if signature is valid, False otherwise
        """
        if not self.webhook_secret:
            logger.error("Webhook secret not configured")
            return False
        
        if not signature:
            logger.warning("No signature provided in webhook request")
            return False
        
        try:
            # Calculate expected signature
            expected = base64.b64encode(
                hmac.new(
                    self.webhook_secret.encode('utf-8'),
                    payload,
                    hashlib.sha256
                ).digest()
            ).decode('utf-8')
            
            # Use constant-time comparison to prevent timing attacks
            return hmac.compare_digest(expected, signature)
            
        except Exception as e:
            logger.error(f"Error verifying webhook signature: {e}")
            return False
    
    def verify_verifier_token(self, challenge: str) -> bool:
        """
        Verify the webhook verifier token (optional)
        
        Used during webhook subscription setup to verify endpoint ownership.
        
        Args:
            challenge: Token sent by Intuit for verification
            
        Returns:
            True if token matches configured token
        """
        if not self.webhook_token:
            logger.debug("No webhook token configured, skipping verification")
            return True
        
        return challenge == self.webhook_token
    
    def parse_payload(self, payload: bytes) -> Optional[WebhookPayload]:
        """
        Parse and validate webhook payload
        
        Args:
            payload: Raw JSON payload bytes
            
        Returns:
            WebhookPayload object or None if invalid
        """
        try:
            data = json.loads(payload)
            
            # Validate payload structure
            if 'eventNotifications' not in data:
                logger.error("Invalid webhook payload: missing eventNotifications")
                return None
            
            events = []
            realm_ids = []
            
            for notification in data['eventNotifications']:
                realm_id = notification.get('realmId')
                if realm_id:
                    realm_ids.append(realm_id)
                
                # Extract events
                data_change = notification.get('dataChange', {})
                entities = data_change.get('entities', [])
                
                for entity in entities:
                    event = WebhookEvent(
                        entity_id=entity.get('id'),
                        entity_type=entity.get('name'),
                        operation=entity.get('operation'),
                        realm_id=realm_id,
                        last_updated=self._parse_timestamp(entity.get('lastUpdated'))
                    )
                    events.append(event)
                    
                    logger.debug(f"Parsed event: {event.operation} {event.entity_type} "
                               f"({event.entity_id}) for realm {realm_id}")
            
            return WebhookPayload(
                events=events,
                realm_ids=list(set(realm_ids)),  # Remove duplicates
                notification_id=data.get('webhooksId')
            )
            
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in webhook payload: {e}")
            return None
        except Exception as e:
            logger.error(f"Error parsing webhook payload: {e}")
            return None
    
    def _parse_timestamp(self, timestamp_str: Optional[str]) -> Optional[datetime]:
        """Parse Intuit timestamp format"""
        if not timestamp_str:
            return None
        try:
            # Intuit timestamps are in ISO 8601 format
            return datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
        except:
            return None
    
    def process_events(self, payload: WebhookPayload) -> Dict:
        """
        Process all events in the webhook payload
        
        Args:
            payload: Parsed webhook payload
            
        Returns:
            Dict with processing results
        """
        results = {
            'total_events': len(payload.events),
            'processed': 0,
            'failed': 0,
            'skipped': 0,
            'by_type': {}
        }
        
        # Group events by realm_id (company) for efficient processing
        events_by_realm: Dict[str, List[WebhookEvent]] = {}
        for event in payload.events:
            if event.realm_id not in events_by_realm:
                events_by_realm[event.realm_id] = []
            events_by_realm[event.realm_id].append(event)
        
        # Process events for each company
        for realm_id, events in events_by_realm.items():
            try:
                company = Company.query.filter_by(realm_id=realm_id).first()
                if not company:
                    logger.warning(f"No company found for realm_id: {realm_id}, skipping events")
                    results['skipped'] += len(events)
                    continue
                
                for event in events:
                    result = self._process_single_event(event, company)
                    
                    # Track results
                    if event.entity_type not in results['by_type']:
                        results['by_type'][event.entity_type] = {'success': 0, 'failed': 0}
                    
                    if result.get('success'):
                        results['processed'] += 1
                        results['by_type'][event.entity_type]['success'] += 1
                    else:
                        results['failed'] += 1
                        results['by_type'][event.entity_type]['failed'] += 1
                        
            except Exception as e:
                logger.error(f"Error processing events for realm {realm_id}: {e}")
                results['failed'] += len(events)
        
        return results
    
    def _process_single_event(self, event: WebhookEvent, company: Company) -> Dict:
        """
        Process a single webhook event
        
        Args:
            event: Webhook event to process
            company: Company associated with the event
            
        Returns:
            Dict with processing result
        """
        logger.info(f"Processing {event.operation} event for {event.entity_type} "
                   f"({event.entity_id}) in company {company.id}")
        
        # Get handler for this entity type
        handler = self.event_handlers.get(event.entity_type)
        
        if not handler:
            logger.debug(f"No handler registered for {event.entity_type}, skipping")
            return {'success': True, 'message': 'No handler registered'}
        
        try:
            return handler(event, company)
        except Exception as e:
            logger.error(f"Error handling event: {e}")
            return {'success': False, 'error': str(e)}
    
    def _handle_account_event(self, event: WebhookEvent, company: Company) -> Dict:
        """
        Handle Account entity changes
        
        Triggers a sync of the affected account or full account sync
        """
        logger.info(f"Handling Account event: {event.operation} {event.entity_id}")
        
        if event.operation == WebhookEventType.DELETE.value:
            # Mark account as deleted in our database
            from app.models.account import Account
            account = Account.query.filter_by(
                company_id=company.id,
                qb_account_id=event.entity_id
            ).first()
            
            if account:
                account.is_active = False
                db.session.commit()
                logger.info(f"Marked account {event.entity_id} as deleted")
                return {'success': True, 'action': 'marked_inactive'}
            
            return {'success': True, 'action': 'account_not_found'}
        
        # For Create/Update, trigger sync
        # In Phase 2, we'll implement targeted sync of just this account
        # For now, we can trigger a full account sync or queue it
        return {
            'success': True, 
            'action': 'sync_triggered',
            'entity_id': event.entity_id,
            'note': 'Full sync placeholder - Phase 2 will implement targeted sync'
        }
    
    def _handle_transaction_event(self, event: WebhookEvent, company: Company) -> Dict:
        """
        Handle Transaction entity changes
        
        Triggers a sync of the affected transaction or transaction range
        """
        logger.info(f"Handling Transaction event: {event.operation} {event.entity_id} "
                   f"({event.entity_type})")
        
        if event.operation == WebhookEventType.DELETE.value:
            # Mark transaction as deleted
            from app.models.transaction import Transaction
            txn = Transaction.query.filter_by(
                company_id=company.id,
                qb_transaction_id=event.entity_id
            ).first()
            
            if txn:
                txn.status = 'deleted'
                db.session.commit()
                logger.info(f"Marked transaction {event.entity_id} as deleted")
                return {'success': True, 'action': 'marked_deleted'}
            
            return {'success': True, 'action': 'transaction_not_found'}
        
        # For Create/Update, queue for sync
        # In Phase 2, we'll fetch just this transaction
        return {
            'success': True,
            'action': 'sync_triggered',
            'entity_id': event.entity_id,
            'entity_type': event.entity_type,
            'note': 'Full sync placeholder - Phase 2 will implement targeted transaction sync'
        }
    
    def _handle_entity_event(self, event: WebhookEvent, company: Company) -> Dict:
        """
        Handle generic entity changes (Customer, Vendor, Item)
        
        These affect transaction matching and categorization
        """
        logger.info(f"Handling Entity event: {event.operation} {event.entity_id} "
                   f"({event.entity_type})")
        
        # Store event for reference but don't trigger immediate action
        # These are used for transaction matching and categorization
        return {
            'success': True,
            'action': 'logged',
            'entity_type': event.entity_type,
            'note': 'Entity change logged for future transaction matching'
        }
    
    def trigger_sync(self, company: Company, entity_types: List[str] = None) -> Dict:
        """
        Trigger a data sync for a company
        
        This is the placeholder for Phase 2 sync integration.
        For now, it logs the intent and can be called manually.
        
        Args:
            company: Company to sync
            entity_types: Optional list of specific entity types to sync
            
        Returns:
            Dict with sync result
        """
        logger.info(f"Sync triggered for company {company.id}, entities: {entity_types}")
        
        # Placeholder for Phase 2
        # In Phase 2, this will:
        # 1. Create a background task for the sync
        # 2. Use CDC to fetch only changed entities
        # 3. Update the database
        # 4. Notify the user of changes
        
        return {
            'success': True,
            'company_id': company.id,
            'entity_types': entity_types,
            'status': 'queued',
            'note': 'Sync queued for Phase 2 implementation'
        }


class WebhookEventLog:
    """
    Logger for webhook events
    
    Stores webhook events in the database for debugging and audit purposes.
    """
    
    @staticmethod
    def log_event(
        notification_id: Optional[str],
        realm_id: str,
        entity_type: str,
        entity_id: str,
        operation: str,
        status: str,
        error_message: Optional[str] = None
    ):
        """
        Log a webhook event
        
        In Phase 2, this will write to a webhook_event_log table.
        For now, it logs to the application logger.
        """
        log_data = {
            'notification_id': notification_id,
            'realm_id': realm_id,
            'entity_type': entity_type,
            'entity_id': entity_id,
            'operation': operation,
            'status': status,
            'error': error_message,
            'timestamp': datetime.utcnow().isoformat()
        }
        
        if error_message:
            logger.error(f"Webhook event failed: {log_data}")
        else:
            logger.info(f"Webhook event processed: {log_data}")
    
    @staticmethod
    def log_delivery(
        notification_id: str,
        payload_size: int,
        event_count: int,
        processing_result: Dict
    ):
        """
        Log webhook delivery summary
        
        Args:
            notification_id: Unique webhook notification ID
            payload_size: Size of payload in bytes
            event_count: Number of events in payload
            processing_result: Dict with processing results
        """
        logger.info(
            f"Webhook delivery: {notification_id} | "
            f"{event_count} events | {payload_size} bytes | "
            f"Processed: {processing_result.get('processed', 0)} | "
            f"Failed: {processing_result.get('failed', 0)}"
        )


# Singleton instance
_webhook_handler: Optional[IntuitWebhookHandler] = None


def get_webhook_handler() -> Optional[IntuitWebhookHandler]:
    """
    Get or create webhook handler singleton
    
    Returns:
        IntuitWebhookHandler instance or None if not configured
    """
    global _webhook_handler
    
    if _webhook_handler is None:
        from flask import current_app
        
        secret = current_app.config.get('INTUIT_WEBHOOK_SECRET')
        token = current_app.config.get('INTUIT_WEBHOOK_TOKEN')
        
        if secret:
            _webhook_handler = IntuitWebhookHandler(secret, token)
        else:
            logger.warning("INTUIT_WEBHOOK_SECRET not configured, webhook verification disabled")
    
    return _webhook_handler
