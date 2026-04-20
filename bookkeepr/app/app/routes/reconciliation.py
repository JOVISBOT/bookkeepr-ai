"""Bank Reconciliation API Routes"""
import csv
import io
from datetime import datetime
from flask import Blueprint, jsonify, request
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename

from app import db
from app.models.bank_statement import BankStatement, BankStatementLine, ReconciliationMatch
from app.models.transaction import Transaction
from app.services.reconciliation import ReconciliationService, get_reconciliation_service

bp = Blueprint('reconciliation', __name__)


ALLOWED_EXTENSIONS = {'csv'}


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@bp.route('/bank-statements', methods=['POST'])
@login_required
def upload_bank_statement():
    """Upload and parse a CSV bank statement"""
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    if not allowed_file(file.filename):
        return jsonify({'error': 'Invalid file type. Only CSV allowed.'}), 400
    
    company_id = request.form.get('company_id', type=int)
    if not company_id:
        return jsonify({'error': 'company_id required'}), 400
    
    # Get optional metadata
    statement_date = request.form.get('statement_date')
    start_balance = request.form.get('start_balance', type=float, default=0)
    end_balance = request.form.get('end_balance', type=float, default=0)
    
    try:
        # Parse CSV
        stream = io.StringIO(file.stream.read().decode('UTF8'), newline=None)
        csv_reader = csv.DictReader(stream)
        
        # Create bank statement record
        statement = BankStatement(
            company_id=company_id,
            file_name=secure_filename(file.filename),
            statement_date=datetime.strptime(statement_date, '%Y-%m-%d').date() if statement_date else None,
            start_balance=start_balance,
            end_balance=end_balance,
            status='processing'
        )
        db.session.add(statement)
        db.session.flush()  # Get ID without committing
        
        # Parse and create bank statement lines
        lines_created = 0
        for row in csv_reader:
            try:
                # Try common CSV column names
                date_str = row.get('Date') or row.get('date') or row.get('Transaction Date') or row.get('Posted Date')
                description = row.get('Description') or row.get('description') or row.get('Payee') or row.get('Memo')
                amount_str = row.get('Amount') or row.get('amount') or row.get('Debit') or row.get('Credit')
                ref_num = row.get('Reference') or row.get('reference') or row.get('Reference Number') or row.get('Check Number')
                
                if not date_str or not amount_str:
                    continue
                
                # Parse date (try multiple formats)
                line_date = None
                for fmt in ['%Y-%m-%d', '%m/%d/%Y', '%d/%m/%Y', '%m-%d-%Y', '%Y/%m/%d']:
                    try:
                        line_date = datetime.strptime(date_str.strip(), fmt).date()
                        break
                    except ValueError:
                        continue
                
                if not line_date:
                    continue
                
                # Parse amount (handle debit/credit columns)
                amount = 0
                try:
                    # Clean amount string
                    amount_clean = amount_str.replace('$', '').replace(',', '').strip()
                    if amount_clean:
                        amount = float(amount_clean)
                except (ValueError, AttributeError):
                    # Try debit/credit split
                    debit = row.get('Debit', '').replace('$', '').replace(',', '').strip()
                    credit = row.get('Credit', '').replace('$', '').replace(',', '').strip()
                    if debit:
                        amount = -float(debit)
                    elif credit:
                        amount = float(credit)
                
                line = BankStatementLine(
                    statement_id=statement.id,
                    line_date=line_date,
                    description=description or '',
                    amount=amount,
                    reference_number=ref_num,
                    match_status='unmatched'
                )
                db.session.add(line)
                lines_created += 1
                
            except Exception as e:
                # Skip problematic rows
                continue
        
        statement.status = 'pending'
        db.session.commit()
        
        return jsonify({
            'success': True,
            'statement': statement.to_dict(),
            'lines_created': lines_created,
            'message': f'Successfully uploaded {lines_created} lines'
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@bp.route('/bank-statements/<int:statement_id>', methods=['GET'])
@login_required
def get_bank_statement(statement_id):
    """Get bank statement details"""
    statement = BankStatement.query.get_or_404(statement_id)
    return jsonify({'statement': statement.to_dict()})


@bp.route('/bank-statements/<int:statement_id>/lines', methods=['GET'])
@login_required
def get_bank_statement_lines(statement_id):
    """Get bank statement lines with match info"""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 50, type=int)
    status = request.args.get('status')  # Filter by match_status
    
    query = BankStatementLine.query.filter_by(statement_id=statement_id)
    
    if status:
        query = query.filter_by(match_status=status)
    
    # Order by date, then by amount
    query = query.order_by(BankStatementLine.line_date.desc(), BankStatementLine.amount.desc())
    
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    
    lines_data = []
    for line in pagination.items:
        line_dict = line.to_dict()
        # Include matched transaction details if exists
        if line.matched_transaction:
            line_dict['matched_transaction'] = {
                'id': line.matched_transaction.id,
                'qbo_transaction_id': line.matched_transaction.qbo_transaction_id,
                'transaction_date': line.matched_transaction.date.isoformat() if line.matched_transaction.date else None,
                'amount': str(line.matched_transaction.amount),
                'description': line.matched_transaction.description,
                'vendor_name': line.matched_transaction.vendor_name
            }
        # Include proposed matches
        proposed = ReconciliationMatch.query.filter_by(
            bank_line_id=line.id,
            status='pending'
        ).order_by(ReconciliationMatch.confidence.desc()).limit(3).all()
        line_dict['proposed_matches'] = [m.to_dict() for m in proposed]
        lines_data.append(line_dict)
    
    return jsonify({
        'lines': lines_data,
        'total': pagination.total,
        'pages': pagination.pages,
        'current_page': page,
        'per_page': per_page
    })


@bp.route('/bank-statements/<int:statement_id>/auto-match', methods=['POST'])
@login_required
def auto_match_statement(statement_id):
    """Run auto-matching on a bank statement"""
    statement = BankStatement.query.get_or_404(statement_id)
    confidence_threshold = request.json.get('confidence_threshold', 0.85) if request.json else 0.85
    
    service = get_reconciliation_service(statement.company_id)
    matches_created = service.auto_match_all(statement_id, confidence_threshold)
    
    return jsonify({
        'success': True,
        'matches_created': matches_created,
        'message': f'Created {matches_created} automatic matches'
    })


@bp.route('/bank-statements/<int:statement_id>/summary', methods=['GET'])
@login_required
def get_statement_summary(statement_id):
    """Get reconciliation summary for a bank statement"""
    statement = BankStatement.query.get_or_404(statement_id)
    
    service = get_reconciliation_service(statement.company_id)
    summary = service.get_reconciliation_summary(statement_id)
    
    return jsonify({'summary': summary})


@bp.route('/reconciliation-matches/<int:match_id>/approve', methods=['POST'])
@login_required
def approve_match(match_id):
    """Approve a reconciliation match"""
    match = ReconciliationMatch.query.get_or_404(match_id)
    
    service = get_reconciliation_service(match.company_id)
    success = service.approve_match(match_id, current_user.id)
    
    if success:
        return jsonify({
            'success': True,
            'message': 'Match approved successfully'
        })
    return jsonify({'error': 'Failed to approve match'}), 400


@bp.route('/reconciliation-matches/<int:match_id>/reject', methods=['POST'])
@login_required
def reject_match(match_id):
    """Reject a reconciliation match"""
    match = ReconciliationMatch.query.get_or_404(match_id)
    
    service = get_reconciliation_service(match.company_id)
    success = service.reject_match(match_id)
    
    if success:
        return jsonify({
            'success': True,
            'message': 'Match rejected successfully'
        })
    return jsonify({'error': 'Failed to reject match'}), 400


@bp.route('/reconciliation/manual-match', methods=['POST'])
@login_required
def create_manual_match():
    """Create a manual match between bank line and transaction"""
    data = request.json
    if not data:
        return jsonify({'error': 'No data provided'}), 400
    
    bank_line_id = data.get('bank_line_id')
    transaction_id = data.get('transaction_id')
    company_id = data.get('company_id')
    
    if not all([bank_line_id, transaction_id, company_id]):
        return jsonify({'error': 'bank_line_id, transaction_id, and company_id required'}), 400
    
    service = get_reconciliation_service(company_id)
    success = service.manual_match(bank_line_id, transaction_id, current_user.id)
    
    if success:
        return jsonify({
            'success': True,
            'message': 'Manual match created successfully'
        })
    return jsonify({'error': 'Failed to create manual match'}), 400


@bp.route('/companies/<int:company_id>/transactions-for-matching', methods=['GET'])
@login_required
def get_transactions_for_matching(company_id):
    """Get transactions available for manual matching"""
    query = request.args.get('query', '')
    date_from = request.args.get('date_from')
    date_to = request.args.get('date_to')
    amount_min = request.args.get('amount_min', type=float)
    amount_max = request.args.get('amount_max', type=float)
    limit = request.args.get('limit', 20, type=int)
    
    q = Transaction.query.filter_by(company_id=company_id)
    
    if date_from:
        q = q.filter(Transaction.date >= datetime.strptime(date_from, '%Y-%m-%d').date())
    if date_to:
        q = q.filter(Transaction.date <= datetime.strptime(date_to, '%Y-%m-%d').date())
    if amount_min is not None:
        q = q.filter(Transaction.amount >= amount_min)
    if amount_max is not None:
        q = q.filter(Transaction.amount <= amount_max)
    if query:
        q = q.filter(Transaction.description.ilike(f'%{query}%'))
    
    q = q.order_by(Transaction.date.desc()).limit(limit)
    
    transactions = [t.to_dict() for t in q.all()]
    return jsonify({'transactions': transactions, 'total': len(transactions)})
