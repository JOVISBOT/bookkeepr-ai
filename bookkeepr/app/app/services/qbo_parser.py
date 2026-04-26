"""QBO/OFX file parser - QuickBooks Web Connect format
.qbo files are OFX 1.0.x SGML format
"""
import re
from datetime import datetime
from decimal import Decimal


def parse_ofx_date(s):
    """OFX date: YYYYMMDD or YYYYMMDDHHMMSS"""
    if not s:
        return None
    s = s.strip()[:8]
    try:
        return datetime.strptime(s, '%Y%m%d').date()
    except ValueError:
        return None


def parse_qbo(content):
    """Parse .qbo / .ofx file content. Returns list of transaction dicts."""
    if isinstance(content, bytes):
        try:
            content = content.decode('utf-8-sig')
        except UnicodeDecodeError:
            content = content.decode('latin-1', errors='ignore')
    
    # Strip OFX header (everything before <OFX>)
    ofx_start = content.find('<OFX>')
    if ofx_start < 0:
        return []
    body = content[ofx_start:]
    
    # Find all <STMTTRN>...</STMTTRN> blocks
    txn_blocks = re.findall(r'<STMTTRN>(.*?)</STMTTRN>', body, re.DOTALL)
    
    transactions = []
    for block in txn_blocks:
        def get_field(tag):
            # SGML allows <TAG>value (no closing) or <TAG>value</TAG>
            m = re.search(rf'<{tag}>([^<\r\n]*)', block, re.IGNORECASE)
            return m.group(1).strip() if m else None
        
        date = parse_ofx_date(get_field('DTPOSTED'))
        amount_str = get_field('TRNAMT')
        try:
            amount = Decimal(amount_str) if amount_str else None
        except Exception:
            amount = None
        
        name = get_field('NAME') or ''
        memo = get_field('MEMO') or ''
        ref = get_field('FITID') or ''
        check_num = get_field('CHECKNUM') or ''
        
        description = ' - '.join(filter(None, [name, memo])) or memo or name
        
        transactions.append({
            'date': date,
            'description': description,
            'amount': amount,
            'vendor': name[:255] if name else None,
            'reference': ref or check_num,
        })
    
    return transactions
