"""RBAC decorators and tenant isolation"""
from functools import wraps
from flask import abort, jsonify, request, g
from flask_login import current_user


def role_required(*roles):
    """Require user to have one of these roles"""
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            if not current_user.is_authenticated:
                if request.path.startswith('/api'):
                    return jsonify({'error': 'Authentication required'}), 401
                abort(401)
            if not current_user.has_role(*roles):
                if request.path.startswith('/api'):
                    return jsonify({'error': f'Forbidden. Required role: {roles}'}), 403
                abort(403)
            return f(*args, **kwargs)
        return wrapper
    return decorator


def operator_required(f):
    """Operator-only routes"""
    @wraps(f)
    def wrapper(*args, **kwargs):
        if not current_user.is_authenticated:
            if request.path.startswith('/api'):
                return jsonify({'error': 'Authentication required'}), 401
            abort(401)
        if not current_user.is_operator and not current_user.is_admin:
            if request.path.startswith('/api'):
                return jsonify({'error': 'Operator access required'}), 403
            abort(403)
        return f(*args, **kwargs)
    return wrapper


def client_required(f):
    """Client portal routes"""
    @wraps(f)
    def wrapper(*args, **kwargs):
        if not current_user.is_authenticated:
            if request.path.startswith('/api'):
                return jsonify({'error': 'Authentication required'}), 401
            abort(401)
        if not current_user.is_client:
            if request.path.startswith('/api'):
                return jsonify({'error': 'Client access required'}), 403
            abort(403)
        return f(*args, **kwargs)
    return wrapper


def tenant_isolated(f):
    """Ensure all queries are scoped to current user's tenant"""
    @wraps(f)
    def wrapper(*args, **kwargs):
        if not current_user.is_authenticated:
            if request.path.startswith('/api'):
                return jsonify({'error': 'Authentication required'}), 401
            abort(401)
        # Set tenant context
        g.tenant_id = current_user.tenant_id
        if not g.tenant_id and not current_user.is_admin:
            if request.path.startswith('/api'):
                return jsonify({'error': 'No tenant assigned'}), 403
            abort(403)
        return f(*args, **kwargs)
    return wrapper


def audit(action, target_table):
    """Auto-log to audit_log"""
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            from app.models import AuditLog
            from extensions import db
            
            result = f(*args, **kwargs)
            
            # Log success
            try:
                AuditLog.log(
                    action=action,
                    target_table=target_table,
                    user=current_user if current_user.is_authenticated else None,
                    request=request,
                )
                db.session.commit()
            except Exception as e:
                print(f"Audit log error: {e}")
            
            return result
        return wrapper
    return decorator
