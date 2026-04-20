"""Add bank reconciliation tables"""
from alembic import op
import sqlalchemy as sa
from datetime import datetime

# Revision identifiers
revision = 'add_bank_reconciliation'
down_revision = None  # Will be set to latest migration


def upgrade():
    # Bank Statements table
    op.create_table('bank_statements',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('company_id', sa.Integer(), sa.ForeignKey('companies.id'), nullable=False),
        sa.Column('file_name', sa.String(255), nullable=False),
        sa.Column('file_path', sa.String(500)),
        sa.Column('upload_date', sa.DateTime(), default=datetime.utcnow),
        sa.Column('statement_date', sa.Date()),
        sa.Column('start_balance', sa.Numeric(12, 2), default=0),
        sa.Column('end_balance', sa.Numeric(12, 2), default=0),
        sa.Column('status', sa.String(20), default='pending')
    )
    
    # Bank Statement Lines table
    op.create_table('bank_statement_lines',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('statement_id', sa.Integer(), sa.ForeignKey('bank_statements.id'), nullable=False),
        sa.Column('line_date', sa.Date(), nullable=False),
        sa.Column('description', sa.String(500)),
        sa.Column('amount', sa.Numeric(12, 2), nullable=False),
        sa.Column('reference_number', sa.String(100)),
        sa.Column('matched_transaction_id', sa.Integer(), sa.ForeignKey('transactions.id')),
        sa.Column('match_confidence', sa.Float(), default=0),
        sa.Column('match_status', sa.String(20), default='unmatched'),
        sa.Column('matched_at', sa.DateTime())
    )
    
    # Reconciliation Matches table
    op.create_table('reconciliation_matches',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('company_id', sa.Integer(), sa.ForeignKey('companies.id'), nullable=False),
        sa.Column('bank_line_id', sa.Integer(), sa.ForeignKey('bank_statement_lines.id'), nullable=False),
        sa.Column('transaction_id', sa.Integer(), sa.ForeignKey('transactions.id'), nullable=False),
        sa.Column('confidence', sa.Float(), nullable=False),
        sa.Column('is_auto_matched', sa.Boolean(), default=False),
        sa.Column('status', sa.String(20), default='pending'),
        sa.Column('created_at', sa.DateTime(), default=datetime.utcnow),
        sa.Column('approved_at', sa.DateTime()),
        sa.Column('approved_by', sa.Integer(), sa.ForeignKey('users.id'))
    )
    
    # Indexes for performance
    op.create_index('idx_bank_lines_statement', 'bank_statement_lines', ['statement_id'])
    op.create_index('idx_bank_lines_status', 'bank_statement_lines', ['match_status'])
    op.create_index('idx_recon_matches_company', 'reconciliation_matches', ['company_id'])
    op.create_index('idx_recon_matches_status', 'reconciliation_matches', ['status'])


def downgrade():
    op.drop_table('reconciliation_matches')
    op.drop_table('bank_statement_lines')
    op.drop_table('bank_statements')
