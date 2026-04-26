"""Cash Flow Forecasting Service"""
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from statistics import mean

from extensions import db
from app.models.transaction import Transaction

logger = logging.getLogger(__name__)


class CashFlowForecaster:
    """Simple cash flow forecasting based on historical transaction patterns"""
    
    def __init__(self, company_id: int):
        self.company_id = company_id
    
    def get_monthly_summary(self, months: int = 6) -> List[Dict[str, Any]]:
        """Get monthly income/expense summary"""
        from sqlalchemy import func, extract
        
        results = db.session.query(
            extract('year', Transaction.transaction_date).label('year'),
            extract('month', Transaction.transaction_date).label('month'),
            func.sum(Transaction.amount).label('total'),
            func.count().label('count')
        ).filter(
            Transaction.company_id == self.company_id,
            Transaction.categorization_status.in_(['categorized', 'suggested'])
        ).group_by(
            extract('year', Transaction.transaction_date),
            extract('month', Transaction.transaction_date)
        ).order_by(
            extract('year', Transaction.transaction_date).desc(),
            extract('month', Transaction.transaction_date).desc()
        ).limit(months).all()
        
        monthly = []
        for row in results:
            date_str = f"{int(row.year)}-{int(row.month):02d}"
            total = float(row.total) if row.total else 0
            monthly.append({
                'month': date_str,
                'total': round(total, 2),
                'income': round(max(0, total), 2),
                'expenses': round(abs(min(0, total)), 2),
                'net': round(total, 2),
                'count': row.count,
            })
        
        monthly.reverse()  # Oldest first
        return monthly
    
    def forecast(self, months_ahead: int = 3) -> Dict[str, Any]:
        """Generate cash flow forecast"""
        historical = self.get_monthly_summary(months=6)
        
        if len(historical) < 2:
            return {
                'success': False,
                'message': 'Need at least 2 months of data for forecasting',
                'forecast': []
            }
        
        # Calculate trends
        nets = [m['net'] for m in historical]
        avg_net = mean(nets)
        
        # Simple trend: use weighted average (recent months weighted more)
        weights = [i + 1 for i in range(len(nets))]
        weighted_avg = sum(n * w for n, w in zip(nets, weights)) / sum(weights)
        
        # Generate forecast
        last_month = datetime.strptime(historical[-1]['month'], '%Y-%m')
        forecast = []
        
        for i in range(1, months_ahead + 1):
            forecast_month = last_month + timedelta(days=30 * i)
            month_str = forecast_month.strftime('%Y-%m')
            
            # Apply slight trend adjustment
            trend_factor = 1.0 + (0.02 * i)  # 2% growth assumption
            predicted_net = weighted_avg * trend_factor
            
            forecast.append({
                'month': month_str,
                'predicted_net': round(predicted_net, 2),
                'predicted_income': round(max(0, predicted_net), 2),
                'predicted_expenses': round(abs(min(0, predicted_net)), 2),
                'confidence': max(0.3, 1.0 - (i * 0.15)),  # Confidence decreases over time
            })
        
        return {
            'success': True,
            'historical': historical,
            'forecast': forecast,
            'average_monthly_net': round(avg_net, 2),
            'trend': 'up' if weighted_avg > avg_net else 'down' if weighted_avg < avg_net else 'stable',
        }
    
    def get_category_breakdown(self, months: int = 3) -> List[Dict[str, Any]]:
        """Get spending breakdown by category"""
        from sqlalchemy import func
        from datetime import datetime as dt
        
        cutoff = dt.utcnow() - timedelta(days=30 * months)
        
        results = db.session.query(
            Transaction.category,
            func.sum(Transaction.amount).label('total'),
            func.count().label('count')
        ).filter(
            Transaction.company_id == self.company_id,
            Transaction.transaction_date >= cutoff,
            Transaction.category.isnot(None)
        ).group_by(
            Transaction.category
        ).all()
        
        breakdown = []
        for row in results:
            total = float(row.total) if row.total else 0
            breakdown.append({
                'category': row.category,
                'total': round(total, 2),
                'count': row.count,
                'is_expense': total < 0,
            })
        
        # Sort by absolute amount
        breakdown.sort(key=lambda x: abs(x['total']), reverse=True)
        return breakdown


def get_forecaster(company_id: int) -> CashFlowForecaster:
    """Factory function for cash flow forecaster"""
    return CashFlowForecaster(company_id)
