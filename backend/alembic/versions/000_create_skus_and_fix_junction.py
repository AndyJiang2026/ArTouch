# AI-ASSISTED: Yes
# AI-TOOL: Claude Code
# PROMPT: Fix missing skus table and cultural_product_videos junction table
# DATE: 2026-04-20
# ENGINEER: System
# RISK-LEVEL: P1

"""Create skus table and fix cultural_product_videos junction table

Revision ID: 000_create_skus_and_fix_junction
Revises:
Create Date: 2026-04-20
"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "000_create_skus_and_fix_junction"
down_revision: str | None = "001_initial"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # =============================================================================
    # 1. Create skus table (MISSING from initial migration!)
    # SKU用于文创品描述关键词（如"白色"、"黑色"），以及NFC URL编码的三位码
    # Foreign key is inline in CREATE TABLE (SQLite compatible)
    # =============================================================================
    op.create_table(
        "skus",
        sa.Column("id", sa.Integer(), nullable=False, primary_key=True, autoincrement=True),
        sa.Column("code", sa.String(length=3), nullable=False, server_default="001"),  # 用于URL编码
        sa.Column("keyword", sa.String(length=100), nullable=False),  # 如"白色"、"黑色"
        sa.Column("cultural_product_id", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        # Foreign key inline (SQLite supports this in CREATE TABLE)
        sa.ForeignKeyConstraint(["cultural_product_id"], ["cultural_products.id"]),
    )
    op.create_index("ix_skus_code", "skus", ["code"], unique=True)
    op.create_index("ix_skus_cultural_product_id", "skus", ["cultural_product_id"])

    # =============================================================================
    # 2. Rename videos_cultural_products -> cultural_product_videos (fix naming mismatch)
    # Model expects 'cultural_product_videos' but migration created 'videos_cultural_products'
    # Only rename if the old table exists (it may not exist in fresh DB)
    # =============================================================================
    try:
        op.execute("ALTER TABLE videos_cultural_products RENAME TO cultural_product_videos")
    except Exception:
        pass  # Table doesn't exist, skip rename


def downgrade() -> None:
    op.execute("ALTER TABLE cultural_product_videos RENAME TO videos_cultural_products")
    op.drop_index("ix_skus_cultural_product_id", "skus")
    op.drop_index("ix_skus_code", "skus")
    op.drop_table("skus")
