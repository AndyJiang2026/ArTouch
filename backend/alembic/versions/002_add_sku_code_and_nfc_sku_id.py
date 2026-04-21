# AI-ASSISTED: Yes
# AI-TOOL: Claude Code
# PROMPT: Add sku.code column and nfc_tags.sku_id column (SQLite compatible)
# DATE: 2026-04-19
# ENGINEER: System
# RISK-LEVEL: P2

"""Add SKU code column and NFC tag SKU relation

Revision ID: 002_add_sku_code_and_nfc_sku_id
Revises: 001_initial
Create Date: 2026-04-19
"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "002_add_sku_code_and_nfc_sku_id"
down_revision: str | None = "000_create_skus_and_fix_junction"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # =============================================================================
    # 1. Add code column to skus table (if not already present)
    # Note: SQLite doesn't support ADD CONSTRAINT, so we use batch mode
    # Note: Migration 000 already creates skus with code column, so skip if exists
    # =============================================================================
    try:
        op.add_column("skus", sa.Column("code", sa.String(length=3), nullable=False, server_default="001"))
        op.create_index("ix_skus_code", "skus", ["code"], unique=True)
    except Exception:
        pass  # Column or index already exists

    # =============================================================================
    # 2. Add sku_id column to nfc_tags table (optional relation to SKU)
    # SQLite requires foreign_keys to be enabled via PRAGMA
    # =============================================================================
    try:
        op.add_column(
            "nfc_tags",
            sa.Column("sku_id", sa.Integer(), nullable=True),
        )
        op.create_index("ix_nfc_tags_sku_id", "nfc_tags", ["sku_id"])
    except Exception:
        pass  # Column already exists

    # SQLite doesn't enforce foreign keys by default, but we add the column
    # For full FK enforcement, the database needs: PRAGMA foreign_keys=ON
    # The column is already added as nullable, which is correct for optional relation


def downgrade() -> None:
    # Drop indexes first
    op.drop_index("ix_nfc_tags_sku_id", "nfc_tags")
    op.drop_index("ix_skus_code", "skus")

    # Drop column
    op.drop_column("nfc_tags", "sku_id")
    op.drop_column("skus", "code")
