"""Client Management Routes - operator manages multiple bookkeeping clients"""
from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify, abort
from flask_login import login_required, current_user
from datetime import datetime
from extensions import db
from app.models import Company, User, Tenant, AuditLog
from app.decorators import operator_required, tenant_isolated

bp = Blueprint('clients', __name__, url_prefix='/clients')


@bp.route('/')
@login_required
@operator_required
def index():
    """List all clients (companies) for current operator's tenant"""
    if not current_user.tenant_id:
        flash('No tenant assigned. Please contact support.', 'error')
        return redirect(url_for('main.index'))
    
    # Get tenant's companies (with health status)
    companies = Company.query.filter_by(
        tenant_id=current_user.tenant_id,
        is_active=True
    ).all()
    
    # Compute health status per client
    client_data = []
    for c in companies:
        # Health rules:
        # GREEN: synced in last 24h, no errors, < 5 uncategorized
        # YELLOW: synced 24-72h ago OR 5-20 uncategorized
        # RED: not synced 72h+ OR > 20 uncategorized OR sync error
        from datetime import timedelta
        now = datetime.utcnow()
        health = 'green'
        health_reasons = []
        
        if not c.is_connected:
            health = 'gray'
            health_reasons.append('Not connected')
        elif c.sync_status == 'error':
            health = 'red'
            health_reasons.append('Sync error')
        elif c.last_sync_at:
            hours_since_sync = (now - c.last_sync_at).total_seconds() / 3600
            if hours_since_sync > 72:
                health = 'red'
                health_reasons.append(f'No sync for {int(hours_since_sync)}h')
            elif hours_since_sync > 24:
                health = 'yellow'
                health_reasons.append(f'Last sync {int(hours_since_sync)}h ago')
        else:
            health = 'yellow'
            health_reasons.append('Never synced')
        
        client_data.append({
            'company': c,
            'health': health,
            'health_reasons': health_reasons,
        })
    
    # Tenant info for limits display
    tenant = Tenant.query.get(current_user.tenant_id)
    
    return render_template('clients/index.html',
                           clients=client_data,
                           tenant=tenant,
                           total=len(client_data))


@bp.route('/new', methods=['GET', 'POST'])
@login_required
@operator_required
def new():
    """Add a new client"""
    tenant = Tenant.query.get(current_user.tenant_id) if current_user.tenant_id else None
    
    if request.method == 'POST':
        if not tenant:
            flash('No tenant found.', 'error')
            return redirect(url_for('clients.index'))
        
        if not tenant.can_add_client():
            flash(f'Plan limit reached. Your {tenant.plan_tier} plan allows {tenant.max_clients} clients. Upgrade to add more.', 'warning')
            return redirect(url_for('pricing.index'))
        
        name = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip()
        phone = request.form.get('phone', '').strip()
        address = request.form.get('address', '').strip()
        
        if not name:
            flash('Client name is required', 'error')
            return render_template('clients/new.html', tenant=tenant)
        
        # Generate placeholder QBO realm ID (will be replaced on real connect)
        import uuid
        placeholder_realm = f'pending-{uuid.uuid4().hex[:12]}'
        
        company = Company(
            user_id=current_user.id,
            tenant_id=current_user.tenant_id,
            qbo_realm_id=placeholder_realm,
            qbo_company_name=name,
            qbo_company_email=email,
            qbo_company_phone=phone,
            qbo_company_address=address,
            is_connected=False,
            is_active=True,
            sync_status='pending',
        )
        db.session.add(company)
        db.session.flush()
        
        # Audit
        AuditLog.log(
            action='create',
            target_table='companies',
            target_id=company.id,
            user=current_user,
            tenant_id=current_user.tenant_id,
            new_value={'name': name, 'email': email},
            request=request,
        )
        db.session.commit()
        
        flash(f'Client "{name}" added! Connect QuickBooks to start syncing.', 'success')
        return redirect(url_for('clients.detail', client_id=company.id))
    
    return render_template('clients/new.html', tenant=tenant)


@bp.route('/<int:client_id>')
@login_required
@operator_required
def detail(client_id):
    """View single client details"""
    company = Company.query.filter_by(
        id=client_id,
        tenant_id=current_user.tenant_id,
    ).first()
    
    if not company:
        abort(404)
    
    # Get recent audit log for this client
    recent_audit = AuditLog.query.filter_by(
        tenant_id=current_user.tenant_id,
        target_table='companies',
        target_id=str(client_id),
    ).order_by(AuditLog.timestamp.desc()).limit(10).all()
    
    return render_template('clients/detail.html',
                           company=company,
                           recent_audit=recent_audit)


@bp.route('/<int:client_id>/edit', methods=['GET', 'POST'])
@login_required
@operator_required
def edit(client_id):
    """Edit client details"""
    company = Company.query.filter_by(
        id=client_id,
        tenant_id=current_user.tenant_id,
    ).first()
    
    if not company:
        abort(404)
    
    if request.method == 'POST':
        old_value = {
            'name': company.qbo_company_name,
            'email': company.qbo_company_email,
            'phone': company.qbo_company_phone,
        }
        
        company.qbo_company_name = request.form.get('name', '').strip() or company.qbo_company_name
        company.qbo_company_email = request.form.get('email', '').strip()
        company.qbo_company_phone = request.form.get('phone', '').strip()
        company.qbo_company_address = request.form.get('address', '').strip()
        
        new_value = {
            'name': company.qbo_company_name,
            'email': company.qbo_company_email,
            'phone': company.qbo_company_phone,
        }
        
        AuditLog.log(
            action='update',
            target_table='companies',
            target_id=company.id,
            user=current_user,
            tenant_id=current_user.tenant_id,
            old_value=old_value,
            new_value=new_value,
            request=request,
        )
        db.session.commit()
        
        flash('Client updated', 'success')
        return redirect(url_for('clients.detail', client_id=client_id))
    
    return render_template('clients/edit.html', company=company)


@bp.route('/<int:client_id>/archive', methods=['POST'])
@login_required
@operator_required
def archive(client_id):
    """Soft-delete client (set is_active=False)"""
    company = Company.query.filter_by(
        id=client_id,
        tenant_id=current_user.tenant_id,
    ).first()
    
    if not company:
        abort(404)
    
    company.is_active = False
    
    AuditLog.log(
        action='archive',
        target_table='companies',
        target_id=company.id,
        user=current_user,
        tenant_id=current_user.tenant_id,
        old_value={'is_active': True},
        new_value={'is_active': False},
        request=request,
    )
    db.session.commit()
    
    flash(f'Client archived', 'info')
    return redirect(url_for('clients.index'))


# JSON API endpoints
@bp.route('/api/list')
@login_required
@operator_required
def api_list():
    """JSON list of clients for AJAX"""
    companies = Company.query.filter_by(
        tenant_id=current_user.tenant_id,
        is_active=True,
    ).all()
    return jsonify({
        'clients': [c.to_dict() for c in companies],
        'count': len(companies),
    })
