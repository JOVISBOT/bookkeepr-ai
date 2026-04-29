"""BookKeepr AI Copilot — chat + function calling via Groq"""
import json
import os
from flask import Blueprint, request, jsonify, current_app
from flask_login import login_required, current_user
from groq import Groq

bp = Blueprint('copilot', __name__)

SYSTEM_PROMPT = """You are BookKeepr AI Copilot, a friendly expert assistant for the BookKeepr AI bookkeeping platform.

You know the app inside out:
- Users can upload bank CSVs, AI auto-categorizes transactions using GAAP standards
- Transactions can be reviewed, approved, rejected, or reclassified
- Reports: Profit & Loss, Balance Sheet, Cash Flow, Trial Balance, General Ledger, A/R Aging, Tax Summary
- Bulk approve lets you approve many transactions at once
- QuickBooks integration syncs data bi-directionally
- MFA (TOTP) is available for security
- Users have a 14-day trial, then need a paid plan (Starter $199/mo, Pro $499/mo, Business $999/mo)

When users ask questions (e.g. "how do I classify a transaction?"), explain clearly with steps.
When users want actions (e.g. "classify #47 as office supplies"), call the appropriate function.

Be conversational but concise. Use the available functions to execute actions when requested. If a function succeeds, confirm to the user. If it fails, explain what went wrong.

Current user info: {user_info}
Current time: {current_time}"""


def _groq_msg_to_dict(msg):
    """Convert a Pydantic ChatCompletionMessage to a plain dict with only Groq-supported fields."""
    if isinstance(msg, dict):
        return msg
    # Access raw message fields directly
    d = {"role": "assistant"}
    if hasattr(msg, 'content') and msg.content:
        d["content"] = msg.content
    if hasattr(msg, 'tool_calls') and msg.tool_calls:
        d["tool_calls"] = [
            {"id": tc.id, "function": {"name": tc.function.name, "arguments": tc.function.arguments}, "type": tc.type or "function"}
            for tc in msg.tool_calls
        ]
    if hasattr(msg, 'name') and msg.name:
        d["name"] = msg.name
    return d


def get_groq_client():
    """Initialize Groq client if API key is available."""
    api_key = os.environ.get('GROQ_API_KEY')
    if not api_key:
        return None
    return Groq(api_key=api_key)


def _call_groq(messages, tools=None):
    """Call Groq with messages and optional tools. Returns response message."""
    client = get_groq_client()
    if not client:
        return {"role": "assistant", "content": "GROQ_API_KEY is not configured. Ask an admin to set it up."}

    kwargs = {
        "model": "llama-3.3-70b-versatile",
        "messages": messages,
        "temperature": 0.3,
        "max_tokens": 1024,
    }
    if tools:
        kwargs["tools"] = tools
        kwargs["tool_choice"] = "auto"

    try:
        resp = client.chat.completions.create(**kwargs)
        return resp.choices[0].message
    except Exception as e:
        current_app.logger.error("Groq API call failed: %s", e)
        return {"role": "assistant", "content": f"Sorry, I hit an error: {str(e)}. Please try again."}


def _tool_result(msg, success=True, data=None):
    """Format a tool result message for Groq."""
    return {
        "role": "tool",
        "tool_call_id": msg.get("tool_calls", [{}])[0].get("id", "unknown"),
        "content": json.dumps({"success": success, "data": data or msg}),
    }


TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "classify_transaction",
            "description": "Reclassify a specific transaction to a new category",
            "parameters": {
                "type": "object",
                "properties": {
                    "transaction_id": {"type": "integer", "description": "Transaction ID to reclassify"},
                    "category": {"type": "string", "description": "New category name (e.g. 'Office Supplies', 'Travel', 'Software')"},
                },
                "required": ["transaction_id", "category"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "ai_categorize_all",
            "description": "Run AI categorization on all uncategorized transactions",
            "parameters": {
                "type": "object",
                "properties": {},
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_report",
            "description": "Get a financial report (P&L, Balance Sheet, Cash Flow, etc.)",
            "parameters": {
                "type": "object",
                "properties": {
                    "report_type": {
                        "type": "string",
                        "enum": ["pnl", "balance", "cashflow", "trial-balance", "ledger", "ar-aging", "tax-summary"],
                        "description": "Type of report",
                    },
                    "start_date": {"type": "string", "description": "Start date (YYYY-MM-DD), optional"},
                    "end_date": {"type": "string", "description": "End date (YYYY-MM-DD), optional"},
                },
                "required": ["report_type"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "bulk_approve",
            "description": "Approve multiple transactions by their IDs",
            "parameters": {
                "type": "object",
                "properties": {
                    "transaction_ids": {
                        "type": "array",
                        "items": {"type": "integer"},
                        "description": "List of transaction IDs to approve",
                    },
                },
                "required": ["transaction_ids"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_transactions",
            "description": "Search or filter transactions",
            "parameters": {
                "type": "object",
                "properties": {
                    "search": {"type": "string", "description": "Search in description/vendor (optional)"},
                    "category_filter": {
                        "type": "string",
                        "enum": ["", "uncategorized", "suggested", "categorized"],
                        "description": "Filter by categorization status",
                    },
                    "status_filter": {
                        "type": "string",
                        "enum": ["", "needs_review", "approved"],
                        "description": "Filter by review status",
                    },
                    "limit": {"type": "integer", "description": "Max results (default 20)"},
                },
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_pending_review_count",
            "description": "Get the number of transactions pending review",
            "parameters": {"type": "object", "properties": {}},
        },
    },
]


@bp.route('/api/copilot', methods=['POST'])
@login_required
def copilot_chat():
    """Chat endpoint: accepts a user message, returns AI response with optional function calls."""
    data = request.get_json(force=True) or {}
    message = data.get('message', '').strip()
    history = data.get('history', [])

    if not message:
        return jsonify({'success': False, 'error': 'Message is required'}), 400

    from datetime import datetime
    user_info = f"Name: {current_user.full_name}, Email: {current_user.email}, Role: {current_user.role}"
    system = SYSTEM_PROMPT.format(
        user_info=user_info,
        current_time=datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC'),
    )

    messages = [{"role": "system", "content": system}]
    for h in history[-10:]:
        messages.append({"role": h.get("role"), "content": h.get("content", "")})
    messages.append({"role": "user", "content": message})

    reply = _call_groq(messages, tools=TOOLS)
    reply = _groq_msg_to_dict(reply)

    # Check if the model wants to call functions
    tool_calls = reply.get('tool_calls')
    if tool_calls:
        messages.append(reply)
        for tc in tool_calls:
            fn = tc['function']
            fn_name = fn['name']
            try:
                fn_args = json.loads(fn.get('arguments', '{}'))
            except (json.JSONDecodeError, TypeError):
                fn_args = {}

            result = _execute_tool(fn_name, fn_args)
            messages.append({
                "role": "tool",
                "tool_call_id": tc['id'],
                "content": json.dumps(result),
            })

        # Get final response after function calls
        reply = _groq_msg_to_dict(_call_groq(messages))

    return jsonify({
        'success': True,
        'reply': reply.get('content', ''),
        'functions_called': [tc['function']['name'] for tc in (tool_calls or [])],
    })


def _execute_tool(fn_name, fn_args):
    """Execute a tool/function and return result data."""
    from app.models.transaction import Transaction
    from app.models.company import Company
    from extensions import db

    try:
        if fn_name == 'classify_transaction':
            txn_id = fn_args.get('transaction_id')
            category = fn_args.get('category')
            txn = Transaction.query.get(txn_id)
            if not txn:
                return {'error': f'Transaction #{txn_id} not found'}
            company = Company.query.filter_by(id=txn.company_id, user_id=current_user.id).first()
            if not company:
                return {'error': 'Transaction not found or access denied'}
            txn.category = category
            txn.categorization_status = 'categorized'
            txn.categorized_by = 'ai'
            db.session.commit()
            return {'message': f'Transaction #{txn_id} reclassified to "{category}"', 'transaction_id': txn_id, 'category': category}

        elif fn_name == 'ai_categorize_all':
            company = Company.query.filter_by(user_id=current_user.id).first()
            if not company:
                return {'error': 'No company found'}
            from app.services.local_classifier import classify as local_classify
            txns = Transaction.query.filter(
                Transaction.company_id == company.id,
                Transaction.categorization_status.in_(['uncategorized', 'suggested'])
            ).all()
            updated = 0
            for txn in txns:
                result = local_classify(txn.description or '', txn.vendor_name or '', float(txn.amount or 0), company.id)
                txn.suggested_category = result['category']
                txn.suggested_confidence = result['confidence']
                txn.categorized_by = 'ai'
                if result['confidence'] >= 80:
                    txn.category = result['category']
                    txn.categorization_status = 'categorized'
                else:
                    txn.categorization_status = 'suggested'
                updated += 1
            db.session.commit()
            return {'message': f'AI categorized {updated} transactions', 'updated': updated}

        elif fn_name == 'get_report':
            report_type = fn_args.get('report_type', 'pnl')
            start_date = fn_args.get('start_date')
            end_date = fn_args.get('end_date')
            from app.routes.reports import generate_pnl_data, generate_balance_data, generate_cashflow_data
            if report_type == 'pnl':
                data = generate_pnl_data(start_date, end_date)
            elif report_type == 'balance':
                data = generate_balance_data(end_date)
            elif report_type == 'cashflow':
                data = generate_cashflow_data('monthly', start_date, end_date)
            else:
                return {'error': f'Report type "{report_type}" not available via copilot'}
            return {'report_type': report_type, 'summary': data.get('summary', {}), 'line_items': data.get('line_items', [])[:10]}

        elif fn_name == 'bulk_approve':
            ids = fn_args.get('transaction_ids', [])
            if not ids:
                return {'error': 'No transaction IDs provided'}
            from datetime import datetime
            company = Company.query.filter_by(user_id=current_user.id, is_active=True).first()
            if not company:
                return {'error': 'No company found'}
            txns = Transaction.query.filter(Transaction.id.in_(ids), Transaction.company_id == company.id).all()
            now = datetime.utcnow()
            approved = 0
            for txn in txns:
                txn.review_status = 'approved'
                txn.reviewed_by_user_id = current_user.id
                txn.reviewed_at = now
                if txn.categorization_status == 'suggested' and txn.suggested_category:
                    txn.category = txn.suggested_category
                    txn.categorization_status = 'categorized'
                approved += 1
            db.session.commit()
            return {'message': f'Approved {approved} transactions', 'approved': approved}

        elif fn_name == 'get_transactions':
            company = Company.query.filter_by(user_id=current_user.id).first()
            if not company:
                return {'error': 'No company found'}
            q = Transaction.query.filter_by(company_id=company.id)
            search = fn_args.get('search', '')
            if search:
                q = q.filter(Transaction.description.ilike(f'%{search}%'))
            cat = fn_args.get('category_filter', '')
            if cat == 'uncategorized':
                q = q.filter_by(categorization_status='uncategorized')
            elif cat == 'suggested':
                q = q.filter_by(categorization_status='suggested')
            elif cat == 'categorized':
                q = q.filter(Transaction.categorization_status != 'uncategorized')
            status = fn_args.get('status_filter', '')
            if status == 'needs_review':
                q = q.filter_by(review_status='pending')
            elif status == 'approved':
                q = q.filter_by(review_status='approved')
            limit = fn_args.get('limit', 20)
            txns = q.order_by(Transaction.transaction_date.desc()).limit(limit).all()
            return {
                'transactions': [{
                    'id': t.id, 'date': str(t.transaction_date), 'description': t.description,
                    'vendor': t.vendor_name, 'amount': float(t.amount or 0),
                    'category': t.category or t.suggested_category or 'Uncategorized',
                    'status': t.categorization_status, 'review_status': t.review_status,
                } for t in txns],
                'total': len(txns),
            }

        elif fn_name == 'get_pending_review_count':
            company = Company.query.filter_by(user_id=current_user.id).first()
            if not company:
                return {'count': 0}
            count = Transaction.query.filter(
                Transaction.company_id == company.id,
                Transaction.categorization_status == 'suggested'
            ).count()
            return {'count': count, 'message': f'{count} transactions pending review'}

        return {'error': f'Unknown function: {fn_name}'}

    except Exception as e:
        current_app.logger.error("Tool %s failed: %s", fn_name, e)
        return {'error': str(e)}
