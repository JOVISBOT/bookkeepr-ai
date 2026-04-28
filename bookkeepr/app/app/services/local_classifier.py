"""
Local transaction classifier — no API calls by default.

Classification priority:
  1. Vendor history     — past approved/categorized transactions with same vendor
  2. Recurring pattern  — same vendor + similar amount on monthly cadence → subscription
  3. Description history — keyword overlap with past transaction descriptions
  4. GAAP rules         — pre-built keyword rules (bootstrap / fallback)
  5. Claude API         — only when confidence < 45 AND |amount| > 100 (edge cases only)
  6. Amount sign        — last-resort fallback

Confidence thresholds:
  >= 80  → auto-categorized (no review needed)
  45-79  → suggested (shown in review queue with explanation)
  < 45   → truly ambiguous → try Claude API, then fallback

Cost design: Claude is called ONLY for transactions where all local methods score < 45
AND the amount is worth the attention (> $100). Expect < 5% of transactions to hit
the API tier once the vendor history grows past ~20 approved transactions.
"""
from __future__ import annotations

import os
import re
import logging
from collections import Counter
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

_STOP_WORDS = {
    'the', 'and', 'for', 'inc', 'llc', 'ltd', 'co', 'corp', 'payment',
    'purchase', 'charge', 'fee', 'from', 'via', 'ref', 'transaction',
    'deposit', 'withdrawal', 'transfer', 'online', 'pos', 'debit', 'credit',
    'sq', 'pp', 'ach', 'www', 'com', 'net', 'org',
}

# Threshold below which we'll try the Claude API (if key is available)
_AI_CONFIDENCE_THRESHOLD = 45
# Minimum absolute amount worth a Claude API call
_AI_AMOUNT_MINIMUM = 100.0


def _tokens(text: str) -> list[str]:
    words = re.findall(r'[a-z]{3,}', text.lower())
    return [w for w in words if w not in _STOP_WORDS]


def classify(description: str, vendor: str, amount: float,
             company_id: int) -> Dict[str, Any]:
    """
    Classify a transaction. Returns:
        {
            'category': str,
            'confidence': float (0-100),
            'source': 'vendor_history' | 'recurring' | 'description_history' |
                      'gaap_rules' | 'claude_api' | 'fallback',
            'explanation': str,
        }
    """
    # 1. Vendor history
    if vendor and vendor.strip():
        result = _vendor_history(vendor.strip(), company_id)
        if result:
            return result

    # 2. Recurring pattern detection
    if vendor and vendor.strip() and amount:
        result = _recurring_pattern(vendor.strip(), float(amount), company_id)
        if result:
            return result

    # 3. Description keyword history
    if description and description.strip():
        result = _description_history(description.strip(), company_id)
        if result:
            return result

    # 4. GAAP rules
    from app.services.gaap_coa import categorize_by_gaap
    gaap = categorize_by_gaap(description or '', vendor or '', amount)
    if gaap.get('keyword_hits', 0) > 0:
        gaap_result = {
            'category': f"{gaap['account_number']} {gaap['account_name']}",
            'account_number': gaap['account_number'],
            'account_name': gaap['account_name'],
            'confidence': gaap['confidence'],
            'source': 'gaap_rules',
            'explanation': gaap.get('explanation', f"GAAP rule: {gaap['account_name']}"),
        }
        # If GAAP confidence is decent, return it
        if gaap['confidence'] >= _AI_CONFIDENCE_THRESHOLD:
            return gaap_result
        # Otherwise fall through to Claude API attempt
        low_confidence_fallback = gaap_result
    else:
        low_confidence_fallback = None

    # 5. Claude API — only for genuinely ambiguous high-value transactions
    abs_amount = abs(float(amount)) if amount else 0
    if abs_amount >= _AI_AMOUNT_MINIMUM and os.getenv('ANTHROPIC_API_KEY'):
        result = _claude_classify(description or '', vendor or '', float(amount))
        if result:
            return result

    # Return low-confidence GAAP result if we have one
    if low_confidence_fallback:
        return low_confidence_fallback

    # 6. Amount-sign fallback
    if amount and float(amount) > 0:
        return {
            'category': '4000 Service Revenue',
            'account_number': '4000',
            'account_name': 'Service Revenue',
            'confidence': 30,
            'source': 'fallback',
            'explanation': 'Positive amount — assumed income',
        }
    return {
        'category': '6999 Miscellaneous Expense',
        'account_number': '6999',
        'account_name': 'Miscellaneous Expense',
        'confidence': 25,
        'source': 'fallback',
        'explanation': 'No pattern found — flagged for review',
    }


def _vendor_history(vendor: str, company_id: int) -> Optional[Dict[str, Any]]:
    """Most common approved category for this vendor."""
    try:
        from extensions import db
        from app.models.transaction import Transaction
        from sqlalchemy import func

        rows = (
            db.session.query(Transaction.category, func.count().label('n'))
            .filter(
                Transaction.company_id == company_id,
                Transaction.review_status == 'approved',
                Transaction.category.isnot(None),
                Transaction.vendor_name.isnot(None),
                func.lower(Transaction.vendor_name).like(f'%{vendor.lower()[:20]}%'),
            )
            .group_by(Transaction.category)
            .order_by(func.count().desc())
            .limit(5)
            .all()
        )

        if not rows:
            return None

        top_cat, top_count = rows[0]
        total = sum(r.n for r in rows)
        if total == 0 or (top_count / total) < 0.6:
            return None

        confidence = 92 if top_count >= 5 else 82 if top_count >= 3 else 68
        return {
            'category': top_cat,
            'confidence': confidence,
            'source': 'vendor_history',
            'explanation': (
                f'Matched vendor "{vendor}" — '
                f'{top_count} past transaction{"s" if top_count != 1 else ""} '
                f'categorized as {top_cat}'
            ),
        }
    except Exception as e:
        logger.warning(f'Vendor history lookup failed: {e}')
        return None


def _recurring_pattern(vendor: str, amount: float, company_id: int) -> Optional[Dict[str, Any]]:
    """
    Detect recurring subscriptions: same vendor, similar amount (within 5%),
    appearing in at least 2 different calendar months.
    Returns a high-confidence Software/Subscription category when detected.
    """
    try:
        from extensions import db
        from app.models.transaction import Transaction
        from sqlalchemy import func, text as sa_text

        # Quick count of distinct months this vendor appeared
        rows = db.session.execute(sa_text('''
            SELECT COUNT(DISTINCT strftime('%Y-%m', transaction_date)) as months,
                   COUNT(*) as total,
                   AVG(ABS(amount)) as avg_amount,
                   category
            FROM transactions
            WHERE company_id = :cid
              AND vendor_name LIKE :vlike
              AND amount < 0
            GROUP BY category
            ORDER BY total DESC
            LIMIT 3
        '''), {'cid': company_id, 'vlike': f'%{vendor[:20]}%'}).fetchall()

        if not rows:
            return None

        best = rows[0]
        months = best[0] or 0
        avg_amount = float(best[2] or 0)
        existing_cat = best[3]

        if months < 2:
            return None

        # Amount must be within 10% of historical average
        if avg_amount > 0 and abs(abs(amount) - avg_amount) / avg_amount > 0.10:
            return None

        # If the vendor already has a consistent category, use it
        if existing_cat:
            return {
                'category': existing_cat,
                'confidence': 85,
                'source': 'recurring',
                'explanation': (
                    f'Recurring charge from "{vendor}" — '
                    f'appeared in {months} months at ~${avg_amount:.0f}/mo'
                ),
            }

        # Otherwise default to Software/Subscriptions (most common recurring type)
        return {
            'category': '6300 Software & Subscriptions',
            'account_number': '6300',
            'account_name': 'Software & Subscriptions',
            'confidence': 75,
            'source': 'recurring',
            'explanation': (
                f'Recurring charge from "{vendor}" — '
                f'appeared in {months} months at ~${avg_amount:.0f}/mo; '
                f'assumed subscription'
            ),
        }
    except Exception as e:
        logger.warning(f'Recurring pattern check failed: {e}')
        return None


def _description_history(description: str, company_id: int) -> Optional[Dict[str, Any]]:
    """Categories from past approved transactions with overlapping description keywords."""
    try:
        from extensions import db
        from app.models.transaction import Transaction

        tokens = _tokens(description)
        if len(tokens) < 2:
            return None

        tokens = sorted(tokens, key=len, reverse=True)[:4]

        rows = (
            db.session.query(Transaction.category, Transaction.description)
            .filter(
                Transaction.company_id == company_id,
                Transaction.review_status == 'approved',
                Transaction.category.isnot(None),
                Transaction.description.isnot(None),
            )
            .limit(500)
            .all()
        )

        if not rows:
            return None

        cat_scores: Counter = Counter()
        for cat, desc in rows:
            past_tokens = set(_tokens(desc))
            overlap = sum(1 for t in tokens if t in past_tokens)
            if overlap >= 2:
                cat_scores[cat] += overlap

        if not cat_scores:
            return None

        top_cat, top_score = cat_scores.most_common(1)[0]
        if top_score < 2:
            return None

        confidence = min(72, 54 + top_score * 3)
        return {
            'category': top_cat,
            'confidence': confidence,
            'source': 'description_history',
            'explanation': f'Description keywords matched past transactions → {top_cat}',
        }
    except Exception as e:
        logger.warning(f'Description history lookup failed: {e}')
        return None


def _claude_classify(description: str, vendor: str, amount: float) -> Optional[Dict[str, Any]]:
    """
    Last-resort Claude API classification for truly ambiguous transactions.
    Called only when all local methods score < 45 AND |amount| >= $100.
    Uses a minimal prompt to keep token usage low.
    """
    try:
        import anthropic
        client = anthropic.Anthropic(api_key=os.getenv('ANTHROPIC_API_KEY'))

        prompt = (
            f'Classify this business transaction into a single US GAAP account category.\n'
            f'Vendor: {vendor or "unknown"}\n'
            f'Description: {description or "none"}\n'
            f'Amount: {"+" if amount > 0 else "-"}${abs(amount):.2f}\n\n'
            f'Reply with ONLY: <account_number> <account_name>\n'
            f'Example: 6100 Office Supplies'
        )

        msg = client.messages.create(
            model='claude-haiku-4-5-20251001',
            max_tokens=30,
            messages=[{'role': 'user', 'content': prompt}],
        )
        raw = msg.content[0].text.strip()

        # Parse "6100 Office Supplies" format
        parts = raw.split(' ', 1)
        if len(parts) == 2 and parts[0].isdigit():
            account_number, account_name = parts[0], parts[1]
            category = f'{account_number} {account_name}'
        else:
            category = raw
            account_number, account_name = '', raw

        return {
            'category': category,
            'account_number': account_number,
            'account_name': account_name,
            'confidence': 65,
            'source': 'claude_api',
            'explanation': f'AI classified "{vendor or description}" → {category}',
        }
    except Exception as e:
        logger.warning(f'Claude API classification failed: {e}')
        return None


# ── Knowledge base helpers ────────────────────────────────────────────────────

def get_vendor_knowledge(company_id: int, limit: int = 50) -> list[Dict[str, Any]]:
    """Learned vendor→category table for the Knowledge Base page."""
    try:
        from extensions import db
        from app.models.transaction import Transaction
        from sqlalchemy import func

        rows = (
            db.session.query(
                Transaction.vendor_name,
                Transaction.category,
                func.count().label('n'),
            )
            .filter(
                Transaction.company_id == company_id,
                Transaction.review_status == 'approved',
                Transaction.vendor_name.isnot(None),
                Transaction.category.isnot(None),
            )
            .group_by(Transaction.vendor_name, Transaction.category)
            .order_by(func.count().desc())
            .limit(limit * 3)
            .all()
        )

        seen: set = set()
        result = []
        for vendor, cat, n in rows:
            if vendor not in seen:
                seen.add(vendor)
                confidence = 92 if n >= 5 else 82 if n >= 3 else 68
                result.append({'vendor': vendor, 'category': cat, 'count': n, 'confidence': confidence})
            if len(result) >= limit:
                break
        return result
    except Exception as e:
        logger.warning(f'get_vendor_knowledge failed: {e}')
        return []


def get_classification_stats(company_id: int) -> Dict[str, Any]:
    """Summary stats for the Knowledge Base page."""
    try:
        from extensions import db
        from app.models.transaction import Transaction
        from sqlalchemy import func

        total = (
            db.session.query(func.count())
            .filter(
                Transaction.company_id == company_id,
                Transaction.review_status == 'approved',
                Transaction.category.isnot(None),
            )
            .scalar() or 0
        )
        unique_vendors = (
            db.session.query(func.count(func.distinct(Transaction.vendor_name)))
            .filter(
                Transaction.company_id == company_id,
                Transaction.review_status == 'approved',
                Transaction.vendor_name.isnot(None),
            )
            .scalar() or 0
        )
        unique_categories = (
            db.session.query(func.count(func.distinct(Transaction.category)))
            .filter(
                Transaction.company_id == company_id,
                Transaction.review_status == 'approved',
                Transaction.category.isnot(None),
            )
            .scalar() or 0
        )
        high_conf_vendors = (
            db.session.query(func.count())
            .filter(
                Transaction.company_id == company_id,
                Transaction.review_status == 'approved',
                Transaction.vendor_name.isnot(None),
            )
            .group_by(Transaction.vendor_name)
            .having(func.count() >= 3)
            .count()
        )

        return {
            'approved_transactions': total,
            'unique_vendors': unique_vendors,
            'high_confidence_vendors': high_conf_vendors,
            'unique_categories': unique_categories,
            'coverage_pct': round(high_conf_vendors / max(unique_vendors, 1) * 100),
        }
    except Exception as e:
        logger.warning(f'get_classification_stats failed: {e}')
        return {
            'approved_transactions': 0, 'unique_vendors': 0,
            'high_confidence_vendors': 0, 'unique_categories': 0, 'coverage_pct': 0,
        }
