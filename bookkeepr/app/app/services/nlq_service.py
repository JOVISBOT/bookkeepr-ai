"""Natural Language Query service — parse English to structured transaction filters."""
import os
import re
import json
from datetime import datetime, timedelta
from typing import Dict, Any


def parse_nl_query(query: str) -> Dict[str, Any]:
    """Parse a natural language query into structured filters for the transaction table."""
    api_key = os.getenv('ANTHROPIC_API_KEY')
    if api_key:
        result = _claude_parse(query, api_key)
        if result:
            return result
    return _pattern_parse(query)


def _claude_parse(query: str, api_key: str) -> Dict[str, Any]:
    try:
        import anthropic
        client = anthropic.Anthropic(api_key=api_key)
        today = datetime.utcnow().strftime('%Y-%m-%d')
        current_month_start = datetime.utcnow().replace(day=1).strftime('%Y-%m-%d')
        last_month_end = (datetime.utcnow().replace(day=1) - timedelta(days=1)).strftime('%Y-%m-%d')
        last_month_start = (datetime.utcnow().replace(day=1) - timedelta(days=1)).replace(day=1).strftime('%Y-%m-%d')
        quarter_start = (datetime.utcnow() - timedelta(days=90)).strftime('%Y-%m-%d')

        prompt = f"""You are a financial query parser. Convert the user's natural language query into a JSON filter object.

Today: {today}
This month starts: {current_month_start}
Last month: {last_month_start} to {last_month_end}
Last 90 days starts: {quarter_start}

Return ONLY a JSON object with any of these optional keys:
- date_from: YYYY-MM-DD
- date_to: YYYY-MM-DD
- min_amount: number (absolute value)
- max_amount: number (absolute value)
- vendor: string (partial match)
- category: string (partial match on category/suggested_category)
- transaction_type: "expense" or "income"
- search: string (free text match on description/vendor)

Examples:
"travel spend last quarter" → {{"date_from":"{quarter_start}","date_to":"{today}","category":"Travel","transaction_type":"expense"}}
"Amazon purchases over $200 this month" → {{"vendor":"Amazon","min_amount":200,"date_from":"{current_month_start}","transaction_type":"expense"}}
"payroll last month" → {{"date_from":"{last_month_start}","date_to":"{last_month_end}","category":"Payroll"}}

Query: {query}

JSON:"""

        msg = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=300,
            messages=[{"role": "user", "content": prompt}]
        )
        text = msg.content[0].text.strip()
        m = re.search(r'\{.*\}', text, re.DOTALL)
        if m:
            return json.loads(m.group())
    except Exception:
        pass
    return {}


def _pattern_parse(query: str) -> Dict[str, Any]:
    """Keyword-based fallback parser."""
    q = query.lower()
    filters: Dict[str, Any] = {}
    today = datetime.utcnow()

    # ── Date ranges ────────────────────────────────────────────────
    if 'last month' in q:
        prev = (today.replace(day=1) - timedelta(days=1))
        filters['date_from'] = prev.replace(day=1).strftime('%Y-%m-%d')
        filters['date_to'] = prev.strftime('%Y-%m-%d')
    elif 'this month' in q:
        filters['date_from'] = today.replace(day=1).strftime('%Y-%m-%d')
        filters['date_to'] = today.strftime('%Y-%m-%d')
    elif 'this year' in q:
        filters['date_from'] = today.replace(month=1, day=1).strftime('%Y-%m-%d')
        filters['date_to'] = today.strftime('%Y-%m-%d')
    elif 'last 90 days' in q or 'last quarter' in q or 'past quarter' in q:
        filters['date_from'] = (today - timedelta(days=90)).strftime('%Y-%m-%d')
        filters['date_to'] = today.strftime('%Y-%m-%d')
    elif 'last 30 days' in q or 'past month' in q:
        filters['date_from'] = (today - timedelta(days=30)).strftime('%Y-%m-%d')
        filters['date_to'] = today.strftime('%Y-%m-%d')
    elif 'last year' in q:
        filters['date_from'] = today.replace(year=today.year - 1, month=1, day=1).strftime('%Y-%m-%d')
        filters['date_to'] = today.replace(year=today.year - 1, month=12, day=31).strftime('%Y-%m-%d')

    # ── Amount thresholds ─────────────────────────────────────────
    m = re.search(r'over\s+\$?([\d,]+)', q)
    if m:
        filters['min_amount'] = float(m.group(1).replace(',', ''))
    m = re.search(r'under\s+\$?([\d,]+)', q)
    if m:
        filters['max_amount'] = float(m.group(1).replace(',', ''))
    m = re.search(r'more than\s+\$?([\d,]+)', q)
    if m:
        filters['min_amount'] = float(m.group(1).replace(',', ''))
    m = re.search(r'less than\s+\$?([\d,]+)', q)
    if m:
        filters['max_amount'] = float(m.group(1).replace(',', ''))

    # ── Category keywords ─────────────────────────────────────────
    cat_map = {
        'travel': 'Travel', 'hotel': 'Travel', 'airline': 'Travel', 'flight': 'Travel',
        'meal': 'Meals', 'food': 'Meals', 'restaurant': 'Meals', 'dining': 'Meals',
        'software': 'Software', 'saas': 'Software', 'subscription': 'Subscriptions',
        'payroll': 'Payroll', 'salary': 'Payroll', 'wage': 'Payroll',
        'marketing': 'Marketing', 'advertising': 'Advertising',
        'insurance': 'Insurance', 'utilities': 'Utilities', 'utility': 'Utilities',
        'rent': 'Rent', 'lease': 'Rent', 'supplies': 'Supplies',
        'consulting': 'Consulting', 'legal': 'Legal', 'accounting': 'Accounting',
        'repair': 'Repairs', 'maintenance': 'Repairs',
    }
    for kw, cat in cat_map.items():
        if kw in q:
            filters['category'] = cat
            break

    # ── Income vs expense ─────────────────────────────────────────
    if any(w in q for w in ['expense', 'spending', 'cost', 'purchase', 'paid', 'spend']):
        filters['transaction_type'] = 'expense'
    elif any(w in q for w in ['income', 'revenue', 'received', 'earned', 'deposit']):
        filters['transaction_type'] = 'income'

    # ── Vendor name (capitalized word after "from" or standalone brand) ────
    m = re.search(r'\bfrom ([A-Z][a-zA-Z0-9 ]+)', query)
    if m:
        filters['vendor'] = m.group(1).strip()
    else:
        # Look for known brands
        brands = ['Amazon', 'Google', 'Microsoft', 'Apple', 'Stripe', 'PayPal', 'Shopify',
                  'Uber', 'Lyft', 'Airbnb', 'Slack', 'Zoom', 'Salesforce', 'Adobe',
                  'QuickBooks', 'Dropbox', 'HubSpot', 'Canva', 'Netflix', 'Spotify']
        for brand in brands:
            if brand.lower() in q:
                filters['vendor'] = brand
                break

    # ── Fallback: use full query as description search ─────────────
    if not filters:
        filters['search'] = query

    return filters
