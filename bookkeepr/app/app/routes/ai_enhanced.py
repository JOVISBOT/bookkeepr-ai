"""Enhanced AI Routes - Anomaly Detection, Cashflow Forecasting"""
from flask import Blueprint, jsonify, request
from flask_login import login_required, current_user

from app.models.company import Company
from app.services.anomaly_detection import get_anomaly_detector
from app.services.cashflow_forecasting import get_forecaster

bp = Blueprint('ai_enhanced', __name__)


@bp.route('/anomalies')
@login_required
def detect_anomalies():
    """Run anomaly detection for user's company"""
    company = Company.query.filter_by(user_id=current_user.id).first()
    if not company:
        return jsonify({'success': False, 'error': 'No company found'}), 404
    
    detector = get_anomaly_detector(company.id)
    results = detector.run_full_scan()
    
    return jsonify({
        'success': True,
        'company_id': company.id,
        **results
    })


@bp.route('/cashflow-forecast')
@login_required
def cashflow_forecast():
    """Get cash flow forecast"""
    company = Company.query.filter_by(user_id=current_user.id).first()
    if not company:
        return jsonify({'success': False, 'error': 'No company found'}), 404
    
    months = request.args.get('months', 3, type=int)
    if months < 1 or months > 12:
        return jsonify({'success': False, 'error': 'Months must be 1-12'}), 422
    
    forecaster = get_forecaster(company.id)
    results = forecaster.forecast(months_ahead=months)
    
    return jsonify(results)


@bp.route('/category-breakdown')
@login_required
def category_breakdown():
    """Get spending breakdown by category"""
    company = Company.query.filter_by(user_id=current_user.id).first()
    if not company:
        return jsonify({'success': False, 'error': 'No company found'}), 404
    
    months = request.args.get('months', 3, type=int)
    
    forecaster = get_forecaster(company.id)
    breakdown = forecaster.get_category_breakdown(months=months)
    
    return jsonify({
        'success': True,
        'breakdown': breakdown,
        'months': months
    })
