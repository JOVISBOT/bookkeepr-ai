"""
Webhook Routes - For QuickBooks webhooks and Stripe webhooks
"""
from flask import Blueprint, request, jsonify, current_app
import logging

from app.services.webhook_handler import (
    get_webhook_handler,
    IntuitWebhookHandler,
    WebhookEventLog
)

logger = logging.getLogger(__name__)
webhooks_bp = Blueprint('webhooks', __name__, url_prefix='/webhooks')


@webhooks_bp.route('/intuit', methods=['POST'])
def intuit_webhook():
    """
    Handle Intuit QuickBooks Online webhooks
    
    Receives real-time notifications when data changes in QBO.
    Verifies webhook signature and processes events.
    
    Reference: https://developer.intuit.com/app/developer/qbo/docs/develop/webhooks
    """
    try:
        # Get raw payload for signature verification
        payload = request.get_data()
        
        # Get signature from header
        signature = request.headers.get('intuit-signature')
        
        logger.info(f"Received Intuit webhook - Signature present: {bool(signature)}")
        
        # Get webhook handler
        handler = get_webhook_handler()
        
        if not handler:
            logger.error("Webhook handler not configured - INTUIT_WEBHOOK_SECRET missing")
            # Still return 200 to prevent Intuit from retrying
            # Log the issue but don't expose internal config errors
            return jsonify({'status': 'received', 'warning': 'handler_not_configured'}), 200
        
        # Verify signature
        if not handler.verify_signature(payload, signature):
            logger.warning("Webhook signature verification failed")
            return jsonify({'error': 'Invalid signature'}), 401
        
        logger.info("Webhook signature verified successfully")
        
        # Parse payload
        webhook_payload = handler.parse_payload(payload)
        
        if not webhook_payload:
            logger.error("Failed to parse webhook payload")
            return jsonify({'error': 'Invalid payload'}), 400
        
        logger.info(f"Parsed webhook payload: {len(webhook_payload.events)} events, "
                   f"realm_ids: {webhook_payload.realm_ids}")
        
        # Log delivery
        WebhookEventLog.log_delivery(
            notification_id=webhook_payload.notification_id or 'unknown',
            payload_size=len(payload),
            event_count=len(webhook_payload.events),
            processing_result={'status': 'received'}
        )
        
        # Process events
        results = handler.process_events(webhook_payload)
        
        logger.info(f"Webhook processing complete: {results}")
        
        # Return success - Intuit expects 200 for successful processing
        return jsonify({
            'status': 'success',
            'processed': results['processed'],
            'failed': results['failed'],
            'skipped': results['skipped'],
            'total_events': results['total_events']
        }), 200
        
    except Exception as e:
        logger.error(f"Webhook processing error: {e}", exc_info=True)
        # Return 500 but Intuit may retry
        return jsonify({'error': 'Processing failed', 'message': str(e)}), 500


@webhooks_bp.route('/qb', methods=['POST'])
def quickbooks_webhook():
    """
    Handle QuickBooks webhooks (legacy endpoint)
    
    This endpoint is deprecated. Please use /webhooks/intuit for new integrations.
    Kept for backward compatibility.
    """
    logger.warning("Legacy /webhooks/qb endpoint called - consider migrating to /webhooks/intuit")
    # Delegate to the Intuit webhook handler
    return intuit_webhook()


@webhooks_bp.route('/stripe', methods=['POST'])
def stripe_webhook():
    """
    Handle Stripe webhooks
    For subscription events
    """
    try:
        payload = request.get_data()
        sig_header = request.headers.get('Stripe-Signature')
        
        logger.info(f"Received Stripe webhook")
        
        # TODO: Verify signature and process events
        # - subscription created/cancelled
        # - payment succeeded/failed
        # - invoice events
        
        return jsonify({'status': 'ok'}), 200
        
    except Exception as e:
        logger.error(f"Stripe webhook error: {e}")
        return jsonify({'error': 'Processing failed'}), 500
