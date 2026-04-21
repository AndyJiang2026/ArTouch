# AI-ASSISTED: Yes
# AI-TOOL: Claude Code
# PROMPT: Add indexes for NFC tag filtering columns
# DATE: 2026-04-20
# ENGINEER: System
# RISK-LEVEL: P1

"""Add indexes for NFC tag filtering columns

Revision ID: 004_add_nfc_tag_indexes
Revises: 003_fix_schema_drift
Create Date: 2026-04-20

This migration adds indexes to improve query performance for:
- NFCTag.status (used in list filtering)
- NFCTag.approval_status (used in dashboard queries)
- tag_clicks.tag_id and tag_clicks.clicked_at (used for time-series analytics)

Note: Some indexes may already exist from migration 001, so we use try/except.
"""

from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "004_add_nfc_tag_indexes"
down_revision: str | None = "003_fix_schema_drift"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # NFCTag status index (used in list filtering)
    try:
        op.create_index("ix_nfc_tags_status", "nfc_tags", ["status"], unique=False)
    except Exception:
        pass  # Index already exists

    # NFCTag approval_status index (used in dashboard and list filtering)
    try:
        op.create_index("ix_nfc_tags_approval_status", "nfc_tags", ["approval_status"], unique=False)
    except Exception:
        pass  # Index already exists

    # tag_clicks indexes for time-series queries
    try:
        op.create_index("ix_tag_clicks_tag_id", "tag_clicks", ["tag_id"], unique=False)
    except Exception:
        pass  # Index already exists

    try:
        op.create_index("ix_tag_clicks_clicked_at", "tag_clicks", ["clicked_at"], unique=False)
    except Exception:
        pass  # Index already exists

    # videos status index for filtering active/inactive videos
    try:
        op.create_index("ix_videos_status", "videos", ["status"], unique=False)
    except Exception:
        pass  # Index already exists

    # Composite index for common NFC tag query pattern
    try:
        op.create_index(
            "ix_nfc_tags_cultural_product_video",
            "nfc_tags",
            ["cultural_product_id", "video_id"],
            unique=False,
        )
    except Exception:
        pass  # Index already exists


def downgrade() -> None:
    try:
        op.drop_index("ix_nfc_tags_cultural_product_video", table_name="nfc_tags")
    except Exception:
        pass
    try:
        op.drop_index("ix_videos_status", table_name="videos")
    except Exception:
        pass
    try:
        op.drop_index("ix_tag_clicks_clicked_at", table_name="tag_clicks")
    except Exception:
        pass
    try:
        op.drop_index("ix_tag_clicks_tag_id", table_name="tag_clicks")
    except Exception:
        pass
    try:
        op.drop_index("ix_nfc_tags_approval_status", table_name="nfc_tags")
    except Exception:
        pass
    try:
        op.drop_index("ix_nfc_tags_status", table_name="nfc_tags")
    except Exception:
        pass
