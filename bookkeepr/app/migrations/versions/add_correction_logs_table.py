"""
Add correction_logs table for AI learning system

Revision ID: add_correction_logs_table
Revises: 
Create Date: 2026-04-19 19:55:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'add_correction_logs_table'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    """Create correction_logs table"""
    op.create_table('correction_logs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('company_id', sa.Integer(), nullable=False),
        sa.Column('transaction_id', sa.Integer(), nullable=False),
        sa.Column('original_account_id', sa.Integer(), nullable=True),
        sa.Column('original_confidence', sa.Float(), nullable=True),
        sa.Column('corrected_account_id', sa.Integer(), nullable=False),
        sa.Column('payee_name', sa.String(length=256), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('amount', sa.Numeric(precision=15, scale=2), nullable=True),
        sa.Column('transaction_type', sa.String(length=50), nullable=True),
        sa.Column('ai_confidence', sa.Float(), nullable=True),
        sa.Column('ai_rules_matched', sa.JSON(), nullable=True),
        sa.Column('correction_pattern', sa.String(length=256), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['company_id'], ['companies.id'], ),
        sa.ForeignKeyConstraint(['corrected_account_id'], ['accounts.id'], ),
        sa.ForeignKeyConstraint(['original_account_id'], ['accounts.id'], ),
        sa.ForeignKeyConstraint(['transaction_id'], ['transactions.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes
    op.create_index('ix_correction_logs_company_id', 'correction_logs', ['company_id'])
    op.create_index('ix_correction_logs_created_at', 'correction_logs', ['created_at'])
    op.create_index('ix_correction_logs_payee_name', 'correction_logs', ['payee_name'])
    op.create_index('ix_correction_logs_transaction_id', 'correction_logs', ['transaction_id'])
    op.create_index('ix_correction_logs_user_id', 'correction_logs', ['user_id'])


def downgrade():
    """Drop correction_logs table"""
    op.drop_index('ix_correction_logs_user_id', table_name='correction_logs')
    op.drop_index('ix_correction_logs_transaction_id', table_name='correction_logs')
    op.drop_index('ix_correction_logs_payee_name', table_name='correction_logs')
    op.drop_index('ix_correction_logs_created_at', table_name='correction_logs')
    op.drop_index('ix_correction_logs_company_id', table_name='correction_logs')
    op.drop_table('correction_logs')
