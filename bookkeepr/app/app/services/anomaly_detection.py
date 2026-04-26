"""Anomaly Detection Service"""
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from statistics import mean, stdev

from extensions import db
from app.models.transaction import Transaction

logger = logging.getLogger(__name__)


class AnomalyDetector:
    """Detect anomalies in financial transactions"""
    
    def __init__(self, company_id: int):
        self.company_id = company_id
        
    def detect_amount_anomalies(self, days: int = 90) -> List[Dict[str, Any]]:
        """Detect transactions with unusually large amounts"""
        cutoff = datetime.utcnow() - timedelta(days=days)
        
        transactions = Transaction.query.filter(
            Transaction.company_id == self.company_id,
            Transaction.transaction_date >= cutoff,
            Transaction.categorization_status.in_(['categorized', 'suggested'])
        ).all()
        
        if len(transactions) < 5:
            return []
        
        # Group by category and find outliers
        by_category = {}
        for txn in transactions:
            cat = txn.category or txn.suggested_category or 'Unknown'
            if cat not in by_category:
                by_category[cat] = []
            by_category[cat].append(abs(float(txn.amount)))
        
        anomalies = []
        for cat, amounts in by_category.items():
            if len(amounts) < 3:
                continue
                
            avg = mean(amounts)
            try:
                std = stdev(amounts)
            except:
                continue
            
            threshold = avg + (2.5 * std)  # 2.5 sigma
            
            for txn in transactions:
                txn_cat = txn.category or txn.suggested_category or 'Unknown'
                if txn_cat == cat and abs(float(txn.amount)) > threshold:
                    anomalies.append({
                        'transaction_id': txn.id,
                        'type': 'amount_outlier',
                        'category': cat,
                        'amount': float(txn.amount),
                        'expected_range': [round(avg - std, 2), round(avg + std, 2)],
                        'severity': 'high' if abs(float(txn.amount)) > avg + (4 * std) else 'medium',
                        'description': f"Amount ${abs(float(txn.amount)):.2f} is unusual for {cat} (typical: ${avg:.2f} ± ${std:.2f})"
                    })
        
        return anomalies
    
    def detect_frequency_anomalies(self, days: int = 90) -> List[Dict[str, Any]]:
        """Detect vendors with unusual transaction frequency"""
        cutoff = datetime.utcnow() - timedelta(days=days)
        
        transactions = Transaction.query.filter(
            Transaction.company_id == self.company_id,
            Transaction.transaction_date >= cutoff,
            Transaction.vendor_name.isnot(None)
        ).all()
        
        if len(transactions) < 10:
            return []
        
        # Count transactions per vendor per month
        from collections import defaultdict
        vendor_monthly = defaultdict(lambda: defaultdict(int))
        
        for txn in transactions:
            month_key = txn.transaction_date.strftime('%Y-%m') if txn.transaction_date else 'unknown'
            vendor_monthly[txn.vendor_name][month_key] += 1
        
        anomalies = []
        for vendor, monthly_counts in vendor_monthly.items():
            counts = list(monthly_counts.values())
            if len(counts) < 2:
                continue
            
            avg_count = mean(counts)
            try:
                std_count = stdev(counts)
            except:
                continue
            
            latest_month = max(monthly_counts.keys())
            latest_count = monthly_counts[latest_month]
            
            if latest_count > avg_count + (2 * std_count) and latest_count > 3:
                anomalies.append({
                    'type': 'frequency_spike',
                    'vendor': vendor,
                    'month': latest_month,
                    'count': latest_count,
                    'typical': round(avg_count, 1),
                    'severity': 'medium',
                    'description': f"{vendor}: {latest_count} transactions in {latest_month} (typical: {avg_count:.1f})"
                })
        
        return anomalies
    
    def detect_duplicate_transactions(self, days: int = 30) -> List[Dict[str, Any]]:
        """Detect potential duplicate transactions"""
        cutoff = datetime.utcnow() - timedelta(days=days)
        
        transactions = Transaction.query.filter(
            Transaction.company_id == self.company_id,
            Transaction.transaction_date >= cutoff
        ).all()
        
        # Group by amount + vendor + date
        from collections import defaultdict
        groups = defaultdict(list)
        
        for txn in transactions:
            key = (
                round(float(txn.amount), 2),
                (txn.vendor_name or '').lower(),
                txn.transaction_date.strftime('%Y-%m-%d') if txn.transaction_date else 'unknown'
            )
            groups[key].append(txn)
        
        anomalies = []
        for key, txns in groups.items():
            if len(txns) > 1:
                anomalies.append({
                    'type': 'potential_duplicate',
                    'amount': key[0],
                    'vendor': key[1],
                    'date': key[2],
                    'count': len(txns),
                    'transaction_ids': [t.id for t in txns],
                    'severity': 'high',
                    'description': f"{len(txns)} transactions of ${key[0]:.2f} from {key[1]} on {key[2]}"
                })
        
        return anomalies
    
    def detect_unusual_hours(self, days: int = 30) -> List[Dict[str, Any]]:
        """Detect transactions at unusual hours (if timestamp available)"""
        # This would check created_at timestamps
        cutoff = datetime.utcnow() - timedelta(days=days)
        
        transactions = Transaction.query.filter(
            Transaction.company_id == self.company_id,
            Transaction.created_at >= cutoff
        ).all()
        
        anomalies = []
        for txn in transactions:
            hour = txn.created_at.hour if txn.created_at else 12
            # Flag transactions created between 11 PM and 5 AM
            if hour >= 23 or hour <= 5:
                anomalies.append({
                    'transaction_id': txn.id,
                    'type': 'unusual_hour',
                    'hour': hour,
                    'severity': 'low',
                    'description': f"Transaction recorded at {hour}:00 (unusual hour)"
                })
        
        return anomalies
    
    def run_full_scan(self) -> Dict[str, Any]:
        """Run all anomaly detection algorithms"""
        amount_anomalies = self.detect_amount_anomalies()
        freq_anomalies = self.detect_frequency_anomalies()
        dup_anomalies = self.detect_duplicate_transactions()
        hour_anomalies = self.detect_unusual_hours()
        
        all_anomalies = (
            amount_anomalies + 
            freq_anomalies + 
            dup_anomalies + 
            hour_anomalies
        )
        
        # Sort by severity
        severity_order = {'high': 0, 'medium': 1, 'low': 2}
        all_anomalies.sort(key=lambda x: severity_order.get(x.get('severity', 'low'), 2))
        
        return {
            'total_anomalies': len(all_anomalies),
            'high_severity': len([a for a in all_anomalies if a.get('severity') == 'high']),
            'medium_severity': len([a for a in all_anomalies if a.get('severity') == 'medium']),
            'low_severity': len([a for a in all_anomalies if a.get('severity') == 'low']),
            'anomalies': all_anomalies[:50],  # Limit to top 50
            'scan_date': datetime.utcnow().isoformat(),
        }


def get_anomaly_detector(company_id: int) -> AnomalyDetector:
    """Factory function for anomaly detector"""
    return AnomalyDetector(company_id)
