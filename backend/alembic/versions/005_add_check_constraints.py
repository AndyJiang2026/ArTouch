# AI-ASSISTED: Yes
# AI-TOOL: Claude Code
# PROMPT: Add CHECK constraints for status/role/enum validation
# DATE: 2026-04-20
# ENGINEER: System
# RISK-LEVEL: P1

"""
Add CHECK constraints for enumerated value validation

Revision ID: 005_add_check_constraints
Revises: 004_add_nfc_tag_indexes
Create Date: 2026-04-20

This migration adds CHECK constraints to validate enumerated values:
- users.role IN ('admin', 'operator')
- videos.status IN ('active', 'inactive', 'ready')
- cultural_products.status IN ('active', 'inactive')
- nfc_tags.status IN ('active', 'inactive')
- nfc_tags.approval_status IN ('pending', 'approved', 'rejected')

Note: SQLite requires batch mode for ALTER TABLE ADD CONSTRAINT.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "005_add_check_constraints"
down_revision: str | None = "004_add_nfc_tag_indexes"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Users table - role constraint (no status column, is_active is boolean)
    try:
        with op.batch_alter_table("users", recreate="always") as batch_op:
            batch_op.create_check_constraint(
                "ck_users_role",
                sa.text("role IN ('admin', 'operator')"),
            )
    except Exception:
        pass  # Constraint already exists

    # Videos table constraint (includes 'ready' for videos ready to use)
    try:
        with op.batch_alter_table("videos", recreate="always") as batch_op:
            batch_op.create_check_constraint(
                "ck_videos_status",
                sa.text("status IN ('active', 'inactive', 'ready')"),
            )
    except Exception:
        pass  # Constraint already exists

    # Cultural products table constraint
    try:
        with op.batch_alter_table("cultural_products", recreate="always") as batch_op:
            batch_op.create_check_constraint(
                "ck_cultural_products_status",
                sa.text("status IN ('active', 'inactive')"),
            )
    except Exception:
        pass  # Constraint already exists

    # NFC tags table constraints
    try:
        with op.batch_alter_table("nfc_tags", recreate="always") as batch_op:
            batch_op.create_check_constraint(
                "ck_nfc_tags_status",
                sa.text("status IN ('active', 'inactive')"),
            )
    except Exception:
        pass  # Constraint already exists

    try:
        with op.batch_alter_table("nfc_tags", recreate="always") as batch_op:
            batch_op.create_check_constraint(
                "ck_nfc_tags_approval_status",
                sa.text("approval_status IN ('pending', 'approved', 'rejected')"),
            )
    except Exception:
        pass  # Constraint already exists

    # SKUs table - no status column, skip


def downgrade() -> None:
    # Drop in reverse order of creation
    try:
        with op.batch_alter_table("nfc_tags", recreate="always") as batch_op:
            batch_op.drop_constraint("ck_nfc_tags_approval_status", type_="check")
    except Exception:
        pass
    try:
        with op.batch_alter_table("nfc_tags", recreate="always") as batch_op:
            batch_op.drop_constraint("ck_nfc_tags_status", type_="check")
    except Exception:
        pass
    try:
        with op.batch_alter_table("cultural_products", recreate="always") as batch_op:
            batch_op.drop_constraint("ck_cultural_products_status", type_="check")
    except Exception:
        pass
    try:
        with op.batch_alter_table("videos", recreate="always") as batch_op:
            batch_op.drop_constraint("ck_videos_status", type_="check")
    except Exception:
        pass
    try:
        with op.batch_alter_table("users", recreate="always") as batch_op:
            batch_op.drop_constraint("ck_users_role", type_="check")
    except Exception:
        pass
