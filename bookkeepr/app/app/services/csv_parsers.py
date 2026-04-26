"""Bank CSV/QBO parsers - handles all major US banks
Reference formats:
  Chase: Details,Posting Date,Description,Amount,Type,Balance,Check or Slip #
  BofA: Date,Description,Amount,Running Bal.
  Wells Fargo: NO HEADERS - Date,Amount,*,blank,Description
  Capital One: Account Number,Transaction Date,Transaction Amount,Transaction Type,Transaction Description,Balance
  US Bank: Date,Transaction,Name,Memo,Amount
  Citibank: Status,Date,Description,Debit,Credit,Member Name
  Mint: Date,Description,Original Description,Amount,Transaction Type,Category,Account Name,Labels,Notes
  PayPal: "Date","Time","TimeZone","Name","Type","Status","Currency","Amount","Receipt ID","Balance"
  Stripe: id,Description,Created (UTC),Amount,Currency,Status,Source,Customer Email...
  QBO web connect (.qbo): OFX format - more complex, separate parser
"""
import io
import csv
import re
from datetime import datetime
from decimal import Decimal, InvalidOperation


# Header keywords mapped to canonical fields (lowercase contains-match)
COLUMN_MAP = {
    'date': [
        'date', 'transaction date', 'posted date', 'trans date', 'posting date',
        'effective date', 'process date', 'created'
    ],
    'description': [
        'description', 'transaction description', 'payee', 'merchant',
        'memo', 'narrative',
        'transaction', 'original description',
    ],
    'amount': [
        'amount', 'value', 'transaction amount', 'sum', 'total',
    ],
    'debit': [
        'debit', 'withdrawal', 'paid out', 'money out', 'expense', 'withdrawals',
    ],
    'credit': [
        'credit', 'deposit', 'paid in', 'money in', 'income', 'deposits',
    ],
    'category': [
        'category', 'classification', 'tag',
    ],
    'vendor': [
        'vendor', 'payee', 'merchant', 'recipient', 'name',
    ],
    'reference': [
        'reference', 'ref', 'check number', 'check #', 'transaction id', 'check or slip', 'id',
    ],
    'type': [
        'type', 'transaction type',
    ],
    'balance': [
        'balance', 'running bal', 'running balance',
    ],
}

DATE_FORMATS = [
    '%Y-%m-%d', '%m/%d/%Y', '%d/%m/%Y', '%m-%d-%Y', '%d-%m-%Y',
    '%Y/%m/%d', '%m/%d/%y', '%d-%b-%Y', '%b %d, %Y', '%B %d, %Y',
    '%Y-%m-%d %H:%M:%S', '%m/%d/%Y %H:%M', '%Y%m%d',
]


def parse_date(value):
    if not value:
        return None
    value = str(value).strip().strip('"')
    if not value:
        return None
    for fmt in DATE_FORMATS:
        try:
            return datetime.strptime(value, fmt).date()
        except ValueError:
            continue
    return None


def parse_amount(value):
    if value is None:
        return None
    s = str(value).strip().strip('"')
    if not s:
        return None
    s = s.replace('$', '').replace(',', '').replace(' ', '')
    if s.startswith('(') and s.endswith(')'):
        s = '-' + s[1:-1]
    try:
        return Decimal(s)
    except InvalidOperation:
        return None


def is_amount_string(value):
    """Strict amount detection: number with optional minus, decimal"""
    if value is None:
        return False
    s = str(value).strip().strip('"').replace('$', '').replace(',', '').replace(' ', '')
    if s.startswith('(') and s.endswith(')'):
        s = s[1:-1]
    if s.startswith('-'):
        s = s[1:]
    if not s:
        return False
    # Must be digits possibly with one dot
    parts = s.split('.')
    if len(parts) > 2:
        return False
    return all(p.isdigit() for p in parts) and any(p.isdigit() for p in parts)


def detect_columns(headers, sample_rows=None):
    """Match column headers; if missing critical fields, infer from sample data"""
    mapping = {}
    headers_lower = [str(h).strip().lower().strip('"') for h in headers]
    
    # 1) Match known header names
    for field, candidates in COLUMN_MAP.items():
        for i, h in enumerate(headers_lower):
            if any(c == h for c in candidates):
                if field not in mapping:
                    mapping[field] = i
                    break
        # Loose match if no exact found
        if field not in mapping:
            for i, h in enumerate(headers_lower):
                if any(c in h for c in candidates):
                    if field not in mapping and i not in mapping.values():
                        mapping[field] = i
                        break
    
    # 2) Infer from sample data if missing critical columns
    if not sample_rows:
        return mapping
    
    sample = sample_rows[0] if sample_rows else []
    
    # Date inference
    if 'date' not in mapping:
        for i, val in enumerate(sample):
            if i in mapping.values():
                continue
            if parse_date(val):
                mapping['date'] = i
                break
    
    # Amount inference (strict numeric check)
    if 'amount' not in mapping and 'debit' not in mapping and 'credit' not in mapping:
        # Find columns where MOST sample rows are numeric
        n_cols = max(len(r) for r in sample_rows[:5]) if sample_rows else 0
        amount_candidates = []
        for col_idx in range(n_cols):
            if col_idx in mapping.values():
                continue
            numeric_count = 0
            for row in sample_rows[:5]:
                if col_idx < len(row) and is_amount_string(row[col_idx]):
                    numeric_count += 1
            if numeric_count >= 3:  # at least 3 of 5 rows
                amount_candidates.append((col_idx, numeric_count))
        if amount_candidates:
            # Pick the one with most matches
            amount_candidates.sort(key=lambda x: -x[1])
            mapping['amount'] = amount_candidates[0][0]
    
    # Description inference: longest text column not used
    if 'description' not in mapping:
        used = set(mapping.values())
        n_cols = max(len(r) for r in sample_rows[:5]) if sample_rows else 0
        best_idx = None
        best_avg_len = 0
        for col_idx in range(n_cols):
            if col_idx in used:
                continue
            lengths = []
            for row in sample_rows[:5]:
                if col_idx < len(row):
                    v = str(row[col_idx]).strip().strip('"')
                    if not parse_date(v) and not is_amount_string(v):
                        lengths.append(len(v))
            if lengths:
                avg = sum(lengths) / len(lengths)
                if avg > best_avg_len and avg > 5:
                    best_avg_len = avg
                    best_idx = col_idx
        if best_idx is not None:
            mapping['description'] = best_idx
    
    return mapping


def looks_like_data_row(row):
    """Determine if a row contains data (not headers)"""
    if not row:
        return False
    has_date = any(parse_date(c) for c in row)
    has_amount = any(is_amount_string(c) for c in row)
    return has_date and has_amount


def parse_csv(content):
    """Parse CSV bytes/string and return (headers, data_rows, col_map)
    
    Auto-detects:
    - Whether first row is a header or data
    - Column mapping for date/description/amount/debit/credit
    - Common bank formats: Chase, BofA, Wells, Capital One, US Bank, Citi, PayPal, Stripe, Mint
    """
    if isinstance(content, bytes):
        # Try utf-8 with BOM, fallback to latin-1
        try:
            content = content.decode('utf-8-sig')
        except UnicodeDecodeError:
            content = content.decode('latin-1', errors='ignore')
    
    # Strip leading blank lines or info preamble
    lines = content.split('\n')
    # Some banks (Wells, Citi) have NO header. Some (Chase) put info above header.
    # Find first row that's CSV-like (has commas)
    start = 0
    for i, line in enumerate(lines):
        if ',' in line:
            start = i
            break
    content = '\n'.join(lines[start:])
    
    reader = csv.reader(io.StringIO(content))
    rows = []
    for r in reader:
        if r and any(str(c).strip() for c in r):
            rows.append(r)
    
    if not rows:
        return [], [], {}
    
    # Decide: first row = headers or data?
    first_row = rows[0]
    if looks_like_data_row(first_row):
        # No header row - generate column names
        headers = [f'Column {i+1}' for i in range(len(first_row))]
        data_rows = rows
    else:
        headers = first_row
        data_rows = rows[1:]
    
    col_map = detect_columns(headers, data_rows[:5] if data_rows else None)
    return headers, data_rows, col_map


def extract_row(row, col_map):
    """Extract canonical fields from a row using col_map
    Returns dict with: date, description, amount, vendor (optional)
    """
    def safe_get(key):
        idx = col_map.get(key)
        if idx is None or idx >= len(row):
            return None
        return str(row[idx]).strip().strip('"')
    
    date = parse_date(safe_get('date'))
    desc = safe_get('description') or ''
    
    # Amount: prefer 'amount', else combine debit/credit
    amount = None
    if col_map.get('amount') is not None:
        amount = parse_amount(safe_get('amount'))
    else:
        debit = parse_amount(safe_get('debit'))
        credit = parse_amount(safe_get('credit'))
        if credit and credit != 0:
            amount = credit
        elif debit and debit != 0:
            amount = -abs(debit)
    
    vendor = safe_get('vendor') or safe_get('reference') or ''
    
    # Strip "*" placeholder values from Wells Fargo
    if desc == '*':
        desc = ''
    if vendor == '*':
        vendor = ''
    
    return {
        'date': date,
        'description': desc,
        'amount': amount,
        'vendor': vendor[:255] if vendor else None,
    }
