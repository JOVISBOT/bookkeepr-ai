"""CSV / QBO Import Routes - supports all major US banks"""
import io
import csv
import json
import os
import uuid
from datetime import datetime
from flask import Blueprint, render_template, request, redirect, url_for, flash, session, jsonify
from flask_login import login_required, current_user
from extensions import db
from app.models import Transaction, Company, AuditLog
from app.services.csv_parsers import parse_csv, extract_row
from app.services.qbo_parser import parse_qbo
from app.services.local_classifier import classify as local_classify

bp = Blueprint('imports', __name__, url_prefix='/imports')

TEMP_DIR = os.path.join(os.path.dirname(__file__), '..', '..', 'instance', 'uploads')
os.makedirs(TEMP_DIR, exist_ok=True)


def get_target_company():
    """Pick connected company first, else first active"""
    company = Company.query.filter_by(
        user_id=current_user.id,
        is_active=True,
        is_connected=True,
    ).first()
    if company:
        return company
    return Company.query.filter_by(user_id=current_user.id, is_active=True).first()


_MAX_UPLOAD_BYTES = 10 * 1024 * 1024  # 10 MB


def _safe_filename(name: str) -> str:
    """Strip path traversal characters from filename."""
    import re
    return re.sub(r'[^a-zA-Z0-9._\-]', '_', os.path.basename(name or ''))


def _scan_csv_injection(raw_bytes: bytes) -> bool:
    """Return True if the file contains formula-injection characters in the first cell of any row."""
    try:
        text = raw_bytes.decode('utf-8', errors='replace')
        for line in text.splitlines():
            first_cell = line.split(',')[0].strip().strip('"')
            if first_cell and first_cell[0] in ('=', '+', '-', '@', '\t', '\r'):
                return True
    except Exception:
        pass
    return False


@bp.route('/csv', methods=['GET', 'POST'])
@login_required
def upload_csv():
    if request.method == 'POST':
        file = request.files.get('csv_file')
        if not file:
            flash('Please choose a file', 'error')
            return redirect(url_for('imports.upload_csv'))

        filename = _safe_filename(file.filename or '').lower()
        if not (filename.endswith('.csv') or filename.endswith('.qbo') or filename.endswith('.ofx')):
            flash('Please upload a .csv, .qbo, or .ofx file', 'error')
            return redirect(url_for('imports.upload_csv'))

        company = get_target_company()
        if not company:
            flash('Add a client first', 'warning')
            return redirect(url_for('clients.new'))

        # Read with size cap — prevents memory exhaustion from huge uploads
        raw = file.read(_MAX_UPLOAD_BYTES + 1)
        if len(raw) > _MAX_UPLOAD_BYTES:
            flash('File is too large. Maximum size is 10 MB.', 'error')
            return redirect(url_for('imports.upload_csv'))

        # Warn on formula injection (CSV injection / Excel macro attack)
        if filename.endswith('.csv') and _scan_csv_injection(raw):
            from flask import current_app
            current_app.logger.warning(
                f'CSV injection pattern detected in upload by user {current_user.id}'
            )
            flash('File contains potentially unsafe content and was rejected.', 'error')
            return redirect(url_for('imports.upload_csv'))
        
        # Parse based on file type
        rows_canonical = []
        if filename.endswith('.csv'):
            headers, data_rows, col_map = parse_csv(raw)
            for r in data_rows:
                rows_canonical.append(extract_row(r, col_map))
        else:
            # .qbo / .ofx
            rows_canonical = parse_qbo(raw)
            headers = ['Date', 'Description', 'Amount', 'Vendor']
            col_map = {'date': 0, 'description': 1, 'amount': 2, 'vendor': 3}
        
        if not rows_canonical:
            flash('No transactions found in file. Check format.', 'error')
            return redirect(url_for('imports.upload_csv'))
        
        # Save to temp
        import_id = f"{current_user.id}_{datetime.now().strftime('%Y%m%d%H%M%S')}_{uuid.uuid4().hex[:6]}"
        temp_path = os.path.join(TEMP_DIR, f"import_{import_id}.json")
        
        # Serialize canonical rows (date -> ISO)
        serialized = []
        for r in rows_canonical:
            serialized.append({
                'date': r['date'].isoformat() if r.get('date') else None,
                'description': r.get('description') or '',
                'amount': float(r['amount']) if r.get('amount') is not None else None,
                'vendor': r.get('vendor'),
            })
        
        with open(temp_path, 'w', encoding='utf-8') as f:
            json.dump({
                'rows': serialized,
                'company_id': company.id,
                'user_id': current_user.id,
                'source_format': 'qbo' if filename.endswith(('.qbo', '.ofx')) else 'csv',
            }, f)
        
        # Build preview (first 10)
        preview = []
        for r in serialized[:10]:
            preview.append({
                **r,
                'valid': bool(r['date'] and r['description'] and r['amount'] is not None),
            })
        
        session['csv_import_id'] = import_id
        
        return render_template(
            'imports/preview.html',
            headers=headers,
            col_map=col_map,
            preview=preview,
            total_rows=len(serialized),
            company=company,
        )
    
    return render_template('imports/upload.html')


@bp.route('/csv/commit', methods=['POST'])
@login_required
def commit_csv():
    import_id = session.get('csv_import_id')
    if not import_id:
        flash('Session expired. Upload again.', 'error')
        return redirect(url_for('imports.upload_csv'))
    
    temp_path = os.path.join(TEMP_DIR, f"import_{import_id}.json")
    if not os.path.exists(temp_path):
        flash('Import file lost. Upload again.', 'error')
        return redirect(url_for('imports.upload_csv'))
    
    with open(temp_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    if data.get('user_id') != current_user.id:
        flash('Access denied', 'error')
        return redirect(url_for('imports.upload_csv'))
    
    company = Company.query.get(data['company_id'])
    if not company or company.user_id != current_user.id:
        flash('Invalid company', 'error')
        return redirect(url_for('imports.upload_csv'))
    
    imported = 0
    skipped = 0
    errors = []
    auto_categorized = 0
    
    for r in data['rows']:
        try:
            date = datetime.fromisoformat(r['date']).date() if r.get('date') else None
            desc = (r.get('description') or '').strip()
            amount = r.get('amount')
            vendor = r.get('vendor')
            
            if not (date and desc and amount is not None):
                skipped += 1
                continue
            
            # Dedupe
            existing = Transaction.query.filter_by(
                company_id=company.id,
                transaction_date=date,
                amount=float(amount),
                description=desc,
            ).first()
            if existing:
                skipped += 1
                continue
            
            txn = Transaction(
                company_id=company.id,
                qbo_transaction_id=f"imp-{uuid.uuid4().hex[:16]}",
                transaction_date=date,
                description=desc[:500],
                amount=float(amount),
                vendor_name=(vendor[:255] if vendor else None),
                transaction_type='income' if amount > 0 else 'expense',
                categorization_status='uncategorized',
                categorized_by='import',
            )
            
            # Auto-categorize using local classifier
            result = local_classify(desc, vendor or '', float(amount), company.id)
            label = result['category']
            confidence = result['confidence']
            txn.suggested_category = label
            txn.suggested_confidence = confidence
            if confidence >= 80:
                txn.category = label
                txn.categorization_status = 'categorized'
                auto_categorized += 1
            else:
                txn.categorization_status = 'suggested'
            txn.raw_data = {
                'ai_explanation': result.get('explanation', label),
                'classification_source': result.get('source', 'local'),
            }
            
            db.session.add(txn)
            imported += 1
        except Exception as e:
            errors.append(str(e)[:100])
    
    AuditLog.log(
        action='csv_import',
        target_table='transactions',
        target_id=company.id,
        user=current_user,
        tenant_id=current_user.tenant_id,
        new_value={'imported': imported, 'auto_categorized': auto_categorized, 'skipped': skipped, 'errors': len(errors), 'source': data.get('source_format', 'csv')},
        request=request,
    )
    db.session.commit()
    
    try:
        os.remove(temp_path)
    except Exception:
        pass
    session.pop('csv_import_id', None)
    
    flash(f'Imported {imported} transactions ({auto_categorized} auto-categorized, {skipped} skipped, {len(errors)} errors)', 'success')
    return redirect(url_for('dashboard.transactions'))


@bp.route('/csv/cancel')
@login_required
def cancel_csv():
    import_id = session.get('csv_import_id')
    if import_id:
        temp_path = os.path.join(TEMP_DIR, f"import_{import_id}.json")
        try:
            os.remove(temp_path)
        except Exception:
            pass
    session.pop('csv_import_id', None)
    flash('Import cancelled', 'info')
    return redirect(url_for('imports.upload_csv'))
