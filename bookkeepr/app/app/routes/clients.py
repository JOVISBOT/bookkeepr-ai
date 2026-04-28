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


@bp.route('/<int:client_id>/invite', methods=['GET', 'POST'])
@login_required
@operator_required
def invite(client_id):
    """Create or reset client portal login credentials"""
    import secrets, string

    company = Company.query.filter_by(
        id=client_id,
        tenant_id=current_user.tenant_id,
    ).first()
    if not company:
        abort(404)

    existing_client = User.query.get(company.client_user_id) if company.client_user_id else None

    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        if not email or '@' not in email:
            flash('Valid email required', 'error')
            return render_template('clients/invite.html', company=company, existing_client=existing_client)

        # Reuse or create client user
        client_user = User.query.filter_by(email=email).first()
        temp_password = None

        if not client_user:
            alphabet = string.ascii_letters + string.digits
            temp_password = ''.join(secrets.choice(alphabet) for _ in range(12))
            client_user = User(
                email=email,
                first_name=request.form.get('first_name', company.qbo_company_name or 'Client').strip(),
                last_name=request.form.get('last_name', '').strip(),
                role='client',
                tenant_id=current_user.tenant_id,
                is_active=True,
            )
            client_user.set_password(temp_password)
            db.session.add(client_user)
            db.session.flush()
        elif client_user.role not in ('client', 'viewer'):
            flash(f'{email} already exists as an operator account.', 'error')
            return render_template('clients/invite.html', company=company, existing_client=existing_client)

        company.client_user_id = client_user.id

        AuditLog.log(
            action='invite_client',
            target_table='companies',
            target_id=company.id,
            user=current_user,
            tenant_id=current_user.tenant_id,
            new_value={'client_email': email},
            request=request,
        )
        db.session.commit()

        if temp_password:
            flash(
                f'Client account created! Email: {email} | Temp Password: {temp_password} — '
                f'Share these credentials securely. Client should change password on first login.',
                'success'
            )
        else:
            flash(f'Existing user {email} linked to {company.qbo_company_name}.', 'success')

        return redirect(url_for('clients.detail', client_id=client_id))

    return render_template('clients/invite.html', company=company, existing_client=existing_client)


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
