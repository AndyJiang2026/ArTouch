"""Add login_count to users table

Revision ID: 007_add_login_count
Revises: 006_add_sku_instances
Create Date: 2026-04-22

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '007_add_login_count'
down_revision = '006_add_sku_instances'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add login_count column with default 0 (for existing users)
    op.add_column('users', sa.Column('login_count', sa.Integer(), nullable=True, server_default='0'))
    # For PostgreSQL, we need to update existing NULL values
    op.execute("UPDATE users SET login_count = 0 WHERE login_count IS NULL")
    # Alter to NOT NULL
    op.alter_column('users', 'login_count', existing_type=sa.Integer(), nullable=False)


def downgrade() -> None:
    op.drop_column('users', 'login_count')
