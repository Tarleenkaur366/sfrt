"""Initial schema migration

Revision ID: 001_initial_schema
Revises: 
Create Date: 2026-10-29 23:30:00.000000

"""
from alembic import op
import sqlalchemy as sa

revision = '001_initial_schema'
down_revision = None
branch_labels = None
depends_on = None

def upgrade() -> None:
    # Users table
    op.create_table(
        'users',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('full_name', sa.String(255), nullable=False),
        sa.Column('email', sa.String(255), nullable=False, unique=True, index=True),
        sa.Column('password_hash', sa.String(255), nullable=False),
        sa.Column('business_name', sa.String(255), nullable=True),
        sa.Column('default_currency', sa.String(10), server_default='INR', nullable=False),
        sa.Column('is_active', sa.Boolean(), server_default='1', nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
    )

    # Categories table
    op.create_table(
        'financial_categories',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('user_id', sa.String(36), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('category_type', sa.String(50), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
    )

    # Transactions table
    op.create_table(
        'financial_transactions',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('user_id', sa.String(36), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('category_id', sa.String(36), sa.ForeignKey('financial_categories.id', ondelete='SET NULL'), nullable=True, index=True),
        sa.Column('transaction_date', sa.Date(), nullable=False, index=True),
        sa.Column('description', sa.String(255), nullable=False, index=True),
        sa.Column('transaction_type', sa.String(50), nullable=False, index=True),
        sa.Column('amount', sa.Numeric(15, 2), nullable=False),
        sa.Column('currency', sa.String(10), server_default='INR', nullable=False),
        sa.Column('payment_method', sa.String(50), nullable=True),
        sa.Column('reference_number', sa.String(100), nullable=True, index=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('is_sample', sa.Boolean(), server_default='0', nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
    )

    # Generated Reports table
    op.create_table(
        'generated_reports',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('user_id', sa.String(36), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('report_type', sa.String(50), nullable=False, index=True),
        sa.Column('title', sa.String(255), nullable=False),
        sa.Column('start_date', sa.Date(), nullable=False),
        sa.Column('end_date', sa.Date(), nullable=False),
        sa.Column('currency', sa.String(10), server_default='INR', nullable=False),
        sa.Column('report_parameters', sa.Text(), nullable=True),
        sa.Column('summary_metrics', sa.Text(), nullable=True),
        sa.Column('detailed_data', sa.Text(), nullable=True),
        sa.Column('generation_status', sa.String(50), server_default='COMPLETED', nullable=False),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
    )

    # Import Jobs table
    op.create_table(
        'import_jobs',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('user_id', sa.String(36), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('file_name', sa.String(255), nullable=False),
        sa.Column('import_type', sa.String(50), server_default='CSV', nullable=False),
        sa.Column('status', sa.String(50), server_default='PENDING', nullable=False),
        sa.Column('total_rows', sa.Integer(), server_default='0', nullable=False),
        sa.Column('successful_rows', sa.Integer(), server_default='0', nullable=False),
        sa.Column('failed_rows', sa.Integer(), server_default='0', nullable=False),
        sa.Column('duplicate_rows', sa.Integer(), server_default='0', nullable=False),
        sa.Column('error_summary', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
    )

    # Audit Logs table
    op.create_table(
        'audit_logs',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('user_id', sa.String(36), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('action', sa.String(50), nullable=False),
        sa.Column('record_type', sa.String(50), nullable=False),
        sa.Column('record_id', sa.String(100), nullable=True),
        sa.Column('details', sa.Text(), nullable=True),
        sa.Column('ip_address', sa.String(50), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
    )

def downgrade() -> None:
    op.drop_table('audit_logs')
    op.drop_table('import_jobs')
    op.drop_table('generated_reports')
    op.drop_table('financial_transactions')
    op.drop_table('financial_categories')
    op.drop_table('users')
