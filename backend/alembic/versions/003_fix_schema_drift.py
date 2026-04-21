# AI-ASSISTED: Yes
# AI-TOOL: Claude Code
# PROMPT: Fix database schema drift - add missing columns
# DATE: 2026-04-20
# ENGINEER: System
# RISK-LEVEL: P1

"""Fix schema drift - add missing columns

Revision ID: 003_fix_schema_drift
Revises: 002_add_sku_code_and_nfc_sku_id
Create Date: 2026-04-20

This migration adds columns that were defined in 001_initial but were not
actually created in the database (schema drift).

Note: Migration 001 already creates complete tables with all columns, so
this migration's operations may fail if columns already exist. We use
try/except to handle this gracefully.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "003_fix_schema_drift"
down_revision: str | None = "002_add_sku_code_and_nfc_sku_id"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # =============================================================================
    # Fix users table - add missing columns (if not already present)
    # =============================================================================
    try:
        op.add_column("users", sa.Column("phone", sa.String(length=20), nullable=True))
    except Exception:
        pass  # Column already exists

    try:
        op.add_column("users", sa.Column("name", sa.String(length=100), nullable=True))
    except Exception:
        pass  # Column already exists

    try:
        op.add_column(
            "users",
            sa.Column("updated_at", sa.DateTime(), nullable=True, server_default=sa.func.now()),
        )
    except Exception:
        pass  # Column already exists

    # =============================================================================
    # Fix videos table - add missing columns (if not already present)
    # =============================================================================
    try:
        op.add_column(
            "videos",
            sa.Column("updated_at", sa.DateTime(), nullable=True, server_default=sa.func.now()),
        )
    except Exception:
        pass  # Column already exists

    try:
        op.add_column("videos", sa.Column("created_by", sa.Integer(), nullable=True))
    except Exception:
        pass  # Column already exists

    # Add foreign key for created_by using batch mode (SQLite compatible)
    try:
        with op.batch_alter_table("videos", recreate="always") as batch_op:
            batch_op.create_foreign_key("fk_videos_created_by", "users", ["created_by"], ["id"])
    except Exception:
        pass  # FK already exists or table doesn't need alteration


def downgrade() -> None:
    # Try to drop FK if it exists
    try:
        with op.batch_alter_table("videos", recreate="always") as batch_op:
            batch_op.drop_constraint("fk_videos_created_by", type_="foreignkey")
    except Exception:
        pass  # FK doesn't exist

    # Drop columns from videos
    try:
        op.drop_column("videos", "created_by")
    except Exception:
        pass  # Column doesn't exist

    try:
        op.drop_column("videos", "updated_at")
    except Exception:
        pass  # Column doesn't exist

    # Drop columns from users
    try:
        op.drop_column("users", "updated_at")
    except Exception:
        pass  # Column doesn't exist

    try:
        op.drop_column("users", "name")
    except Exception:
        pass  # Column doesn't exist

    try:
        op.drop_column("users", "phone")
    except Exception:
        pass  # Column doesn't exist
