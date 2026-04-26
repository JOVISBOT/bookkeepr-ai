"""Audit Log Model - Track every action for compliance"""
from datetime import datetime
from extensions import db


class AuditLog(db.Model):
    """Immutable audit trail for compliance and debugging"""
    
    __tablename__ = 'audit_log'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # Multi-tenant
    tenant_id = db.Column(db.Integer, db.ForeignKey('tenants.id'), nullable=True, index=True)
    
    # Who
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True, index=True)
    user_email = db.Column(db.String(255))  # snapshot in case user is deleted
    
    # What
    action = db.Column(db.String(50), nullable=False, index=True)  # 'create', 'update', 'delete', 'login', 'export'
    target_table = db.Column(db.String(50), nullable=False, index=True)  # 'transactions', 'users'
    target_id = db.Column(db.String(50))  # the affected record id
    
    # Changes (JSON)
    old_value = db.Column(db.JSON)
    new_value = db.Column(db.JSON)
    
    # Context
    ip_address = db.Column(db.String(45))  # IPv6 max
    user_agent = db.Column(db.String(500))
    
    # When
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    
    def __repr__(self):
        return f'<AuditLog {self.action} {self.target_table}:{self.target_id} by user:{self.user_id}>'
    
    @classmethod
    def log(cls, action, target_table, target_id=None, user=None, tenant_id=None, 
            old_value=None, new_value=None, request=None):
        """Create an audit log entry"""
        try:
            entry = cls(
                action=action,
                target_table=target_table,
                target_id=str(target_id) if target_id else None,
                user_id=user.id if user else None,
                user_email=user.email if user else None,
                tenant_id=tenant_id or (user.tenant_id if user else None),
                old_value=old_value,
                new_value=new_value,
            )
            if request:
                entry.ip_address = request.remote_addr
                entry.user_agent = request.headers.get('User-Agent', '')[:500]
            db.session.add(entry)
            db.session.flush()
            return entry
        except Exception as e:
            # Don't break the main action if audit fails
            db.session.rollback()
            print(f"Audit log error: {e}")
            return None
    
    def to_dict(self):
        return {
            'id': self.id,
            'tenant_id': self.tenant_id,
            'user_id': self.user_id,
            'user_email': self.user_email,
            'action': self.action,
            'target_table': self.target_table,
            'target_id': self.target_id,
            'old_value': self.old_value,
            'new_value': self.new_value,
            'ip_address': self.ip_address,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None,
        }
