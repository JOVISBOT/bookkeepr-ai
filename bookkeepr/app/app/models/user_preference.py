"""User Preferences Model"""
from extensions import db


class UserPreference(db.Model):
    __tablename__ = 'user_preferences'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), unique=True, nullable=False, index=True)

    # AI settings
    auto_categorization = db.Column(db.Boolean, default=True)
    confidence_threshold = db.Column(db.Integer, default=80)

    # Notification settings
    notify_daily_summary = db.Column(db.Boolean, default=True)
    notify_uncategorized = db.Column(db.Boolean, default=True)
    notify_monthly_reports = db.Column(db.Boolean, default=False)
    notify_anomalies = db.Column(db.Boolean, default=False)

    user = db.relationship('User', backref=db.backref('preferences', uselist=False))
