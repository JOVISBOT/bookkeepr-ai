"""Bank Reconciliation Matching Service"""
from datetime import datetime, timedelta
from rapidfuzz import fuzz
from sqlalchemy import or_
from app import db
from app.models.transaction import Transaction
from app.models.bank_statement import BankStatementLine, ReconciliationMatch


class ReconciliationService:
    """Service for matching bank statements with QBO transactions"""
    
    def __init__(self, company_id):
        self.company_id = company_id
    
    def find_matches(self, bank_line, min_confidence=0.7):
        """
        Find potential transaction matches for a bank statement line
        Returns list of (transaction, confidence_score) tuples
        """
        matches = []
        
        # Get transactions within date range (±3 days)
        date_min = bank_line.line_date - timedelta(days=3)
        date_max = bank_line.line_date + timedelta(days=3)
        
        # Get unmatched or unmatched transactions
        candidates = Transaction.query.filter(
            Transaction.company_id == self.company_id,
            Transaction.date >= date_min,
            Transaction.date <= date_max
        ).all()
        
        for transaction in candidates:
            score = self._calculate_match_score(bank_line, transaction)
            if score >= min_confidence:
                matches.append((transaction, score))
        
        # Sort by confidence (highest first)
        matches.sort(key=lambda x: x[1], reverse=True)
        return matches
    
    def _calculate_match_score(self, bank_line, transaction):
        """Calculate match confidence score (0-1)"""
        score = 0.0
        
        # Amount match (exact = 0.4, within 0.01 = 0.35, within 0.1 = 0.2)
        amount_diff = abs(float(bank_line.amount) - float(transaction.amount))
        if amount_diff < 0.01:
            score += 0.4
        elif amount_diff < 0.1:
            score += 0.2
        elif amount_diff < 1.0:
            score += 0.1
        
        # Date proximity (within 1 day = 0.3, 3 days = 0.2, 5 days = 0.1)
        date_diff = abs((bank_line.line_date - transaction.date).days)
        if date_diff == 0:
            score += 0.3
        elif date_diff <= 1:
            score += 0.25
        elif date_diff <= 3:
            score += 0.2
        elif date_diff <= 5:
            score += 0.1
        
        # Description similarity using fuzzy matching
        if bank_line.description and transaction.description:
            desc_score = fuzz.ratio(
                bank_line.description.lower(),
                transaction.description.lower()
            ) / 100.0
            score += desc_score * 0.3
        
        return min(score, 1.0)
    
    def auto_match_all(self, statement_id, confidence_threshold=0.85):
        """Automatically match all unmatched lines with high confidence"""
        lines = BankStatementLine.query.filter(
            BankStatementLine.statement_id == statement_id,
            BankStatementLine.match_status == 'unmatched'
        ).all()
        
        matches_created = 0
        
        for line in lines:
            matches = self.find_matches(line, min_confidence=confidence_threshold)
            
            if matches:
                best_match, confidence = matches[0]
                
                # Create match record
                match = ReconciliationMatch(
                    company_id=self.company_id,
                    bank_line_id=line.id,
                    transaction_id=best_match.id,
                    confidence=confidence,
                    is_auto_matched=True,
                    status='pending'
                )
                db.session.add(match)
                
                # Update bank line
                line.match_status = 'matched'
                line.matched_transaction_id = best_match.id
                line.match_confidence = confidence
                
                matches_created += 1
        
        db.session.commit()
        return matches_created
    
    def get_reconciliation_summary(self, statement_id):
        """Get summary stats for a bank statement"""
        lines = BankStatementLine.query.filter_by(statement_id=statement_id).all()
        
        total = len(lines)
        matched = sum(1 for l in lines if l.match_status == 'matched')
        approved = sum(1 for l in lines if l.match_status == 'approved')
        rejected = sum(1 for l in lines if l.match_status == 'rejected')
        unmatched = total - matched - approved - rejected
        
        # Calculate totals
        total_in = sum(float(l.amount) for l in lines if float(l.amount) > 0)
        total_out = sum(float(l.amount) for l in lines if float(l.amount) < 0)
        
        return {
            'total_lines': total,
            'matched': matched,
            'approved': approved,
            'rejected': rejected,
            'unmatched': unmatched,
            'total_in': total_in,
            'total_out': total_out,
            'match_rate': (matched + approved) / total if total > 0 else 0
        }
    
    def approve_match(self, match_id, user_id):
        """Approve a proposed match"""
        match = ReconciliationMatch.query.get(match_id)
        if not match or match.company_id != self.company_id:
            return False
        
        match.status = 'approved'
        match.approved_at = datetime.utcnow()
        match.approved_by = user_id
        
        # Update bank line
        match.bank_line.match_status = 'approved'
        
        db.session.commit()
        return True
    
    def reject_match(self, match_id):
        """Reject a proposed match"""
        match = ReconciliationMatch.query.get(match_id)
        if not match or match.company_id != self.company_id:
            return False
        
        match.status = 'rejected'
        
        # Update bank line back to unmatched
        match.bank_line.match_status = 'unmatched'
        match.bank_line.matched_transaction_id = None
        match.bank_line.match_confidence = 0
        
        db.session.commit()
        return True
    
    def manual_match(self, bank_line_id, transaction_id, user_id):
        """Manually match a bank line to a transaction"""
        line = BankStatementLine.query.get(bank_line_id)
        transaction = Transaction.query.get(transaction_id)
        
        if not line or not transaction:
            return False
        
        if transaction.company_id != self.company_id:
            return False
        
        # Create manual match with high confidence
        match = ReconciliationMatch(
            company_id=self.company_id,
            bank_line_id=bank_line_id,
            transaction_id=transaction_id,
            confidence=1.0,  # Manual matches are 100%
            is_auto_matched=False,
            status='approved',
            approved_at=datetime.utcnow(),
            approved_by=user_id
        )
        db.session.add(match)
        
        # Update line
        line.match_status = 'approved'
        line.matched_transaction_id = transaction_id
        line.match_confidence = 1.0
        line.matched_at = datetime.utcnow()
        
        db.session.commit()
        return True


def get_reconciliation_service(company_id):
    """Factory function to get reconciliation service"""
    return ReconciliationService(company_id)
