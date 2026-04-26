"""
Smart Reconciliation Service
Automatically matches transactions with bank statements
Detects duplicates, discrepancies, and anomalies
"""
import difflib
from datetime import datetime, timedelta
from typing import List, Dict, Tuple, Optional
from collections import defaultdict

class SmartReconciliation:
    """AI-powered bank reconciliation"""
    
    def __init__(self):
        self.match_threshold = 0.85  # 85% similarity for fuzzy matching
        self.date_tolerance = 3  # 3 days tolerance
        
    def find_matches(self, transactions: List[Dict], bank_transactions: List[Dict]) -> Dict:
        """
        Match book transactions with bank transactions
        
        Returns:
            {
                'matched': [(trans_id, bank_trans_id, confidence), ...],
                'unmatched_book': [trans_id, ...],
                'unmatched_bank': [bank_trans_id, ...],
                'duplicates': [(trans_id, bank_trans_id), ...],
                'discrepancies': [(trans_id, bank_trans_id, difference), ...]
            }
        """
        matches = []
        unmatched_book = []
        unmatched_bank = list(range(len(bank_transactions)))
        duplicates = []
        discrepancies = []
        
        used_bank_indices = set()
        
        for t_idx, trans in enumerate(transactions):
            best_match = None
            best_score = 0
            best_b_idx = -1
            
            for b_idx, bank_trans in enumerate(bank_transactions):
                if b_idx in used_bank_indices:
                    continue
                    
                score = self._calculate_match_score(trans, bank_trans)
                
                if score > best_score:
                    best_score = score
                    best_match = bank_trans
                    best_b_idx = b_idx
            
            if best_score >= self.match_threshold:
                matches.append((t_idx, best_b_idx, best_score))
                used_bank_indices.add(best_b_idx)
                unmatched_bank.remove(best_b_idx)
                
                # Check for discrepancy in amount
                amount_diff = abs(trans.get('amount', 0) - best_match.get('amount', 0))
                if amount_diff > 0.01:
                    discrepancies.append((t_idx, best_b_idx, amount_diff))
            else:
                unmatched_book.append(t_idx)
        
        # Check for duplicates in matched transactions
        matched_amounts = defaultdict(list)
        for t_idx, b_idx, score in matches:
            amount = round(transactions[t_idx].get('amount', 0), 2)
            matched_amounts[amount].append((t_idx, b_idx))
        
        for amount, pairs in matched_amounts.items():
            if len(pairs) > 1:
                # Mark all but first as duplicates
                for t_idx, b_idx in pairs[1:]:
                    duplicates.append((t_idx, b_idx))
        
        return {
            'matched': matches,
            'unmatched_book': unmatched_book,
            'unmatched_bank': unmatched_bank,
            'duplicates': duplicates,
            'discrepancies': discrepancies
        }
    
    def _calculate_match_score(self, trans: Dict, bank_trans: Dict) -> float:
        """Calculate match confidence score (0-1)"""
        scores = []
        
        # Amount matching (weight: 40%)
        amount_diff = abs(trans.get('amount', 0) - bank_trans.get('amount', 0))
        amount_score = max(0, 1 - (amount_diff / max(abs(trans.get('amount', 1)), 1)))
        scores.append(('amount', amount_score, 0.40))
        
        # Date matching (weight: 30%)
        date1 = self._parse_date(trans.get('date'))
        date2 = self._parse_date(bank_trans.get('date'))
        if date1 and date2:
            date_diff = abs((date1 - date2).days)
            date_score = max(0, 1 - (date_diff / self.date_tolerance))
            scores.append(('date', date_score, 0.30))
        
        # Description matching (weight: 30%)
        desc1 = trans.get('description', '')
        desc2 = bank_trans.get('description', '')
        if desc1 and desc2:
            # Fuzzy string matching
            similarity = difflib.SequenceMatcher(None, desc1.lower(), desc2.lower()).ratio()
            scores.append(('description', similarity, 0.30))
        
        # Calculate weighted score
        total_weight = sum(weight for _, _, weight in scores)
        weighted_score = sum(score * weight for _, score, weight in scores) / total_weight if total_weight > 0 else 0
        
        return weighted_score
    
    def detect_anomalies(self, transactions: List[Dict]) -> List[Dict]:
        """Detect unusual transactions that need review"""
        anomalies = []
        
        if not transactions:
            return anomalies
        
        # Group by vendor/merchant
        vendor_amounts = defaultdict(list)
        for trans in transactions:
            vendor = trans.get('vendor_name') or trans.get('merchant_name') or trans.get('description', '')
            vendor_amounts[vendor].append(trans.get('amount', 0))
        
        # Check for outliers using standard deviation
        for trans in transactions:
            vendor = trans.get('vendor_name') or trans.get('merchant_name') or trans.get('description', '')
            amounts = vendor_amounts[vendor]
            
            if len(amounts) >= 3:
                mean = sum(amounts) / len(amounts)
                variance = sum((x - mean) ** 2 for x in amounts) / len(amounts)
                std_dev = variance ** 0.5
                
                amount = trans.get('amount', 0)
                if std_dev > 0:
                    z_score = abs(amount - mean) / std_dev
                    
                    # Flag if more than 2 standard deviations
                    if z_score > 2:
                        anomalies.append({
                            'transaction': trans,
                            'type': 'amount_outlier',
                            'reason': f'Amount ${amount:.2f} is {z_score:.1f} std dev from average ${mean:.2f}',
                            'severity': 'high' if z_score > 3 else 'medium'
                        })
        
        # Check for round numbers (possible fraud indicator)
        for trans in transactions:
            amount = trans.get('amount', 0)
            if amount > 100 and amount == int(amount) and amount % 100 == 0:
                anomalies.append({
                    'transaction': trans,
                    'type': 'round_number',
                    'reason': f'Round number amount: ${amount:.2f}',
                    'severity': 'low'
                })
        
        # Check for duplicate amounts on same day
        date_amounts = defaultdict(list)
        for trans in transactions:
            date = trans.get('date')
            amount = round(trans.get('amount', 0), 2)
            date_amounts[(date, amount)].append(trans)
        
        for (date, amount), trans_list in date_amounts.items():
            if len(trans_list) > 1:
                for trans in trans_list:
                    anomalies.append({
                        'transaction': trans,
                        'type': 'duplicate_amount',
                        'reason': f'Duplicate ${amount:.2f} on {date}',
                        'severity': 'medium'
                    })
        
        return anomalies
    
    def generate_reconciliation_report(self, matches: Dict, book_balance: float, bank_balance: float) -> Dict:
        """Generate a comprehensive reconciliation report"""
        matched_count = len(matches['matched'])
        unmatched_book_count = len(matches['unmatched_book'])
        unmatched_bank_count = len(matches['unmatched_bank'])
        duplicate_count = len(matches['duplicates'])
        discrepancy_count = len(matches['discrepancies'])
        
        # Calculate difference
        difference = abs(book_balance - bank_balance)
        
        # Determine status
        if difference < 0.01 and unmatched_book_count == 0 and unmatched_bank_count == 0:
            status = 'balanced'
        elif difference < 1.00:
            status = 'minor_difference'
        else:
            status = 'needs_review'
        
        return {
            'status': status,
            'book_balance': book_balance,
            'bank_balance': bank_balance,
            'difference': difference,
            'matched_transactions': matched_count,
            'unmatched_book': unmatched_book_count,
            'unmatched_bank': unmatched_bank_count,
            'duplicates_found': duplicate_count,
            'discrepancies': discrepancy_count,
            'is_balanced': status == 'balanced'
        }
    
    def _parse_date(self, date_str) -> Optional[datetime]:
        """Parse date string to datetime"""
        if not date_str:
            return None
        
        if isinstance(date_str, datetime):
            return date_str
        
        formats = [
            '%Y-%m-%d',
            '%m/%d/%Y',
            '%m-%d-%Y',
            '%Y/%m/%d',
            '%d-%m-%Y',
        ]
        
        for fmt in formats:
            try:
                return datetime.strptime(date_str, fmt)
            except ValueError:
                continue
        
        return None


# Create singleton instance
reconciliation_service = SmartReconciliation()
