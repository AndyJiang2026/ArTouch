# AI-ASSISTED: Yes
# AI-TOOL: Claude Code
# PROMPT: Create initial database migration
# DATE: 2026-04-19
# ENGINEER: System
# RISK-LEVEL: P2

"""Initial migration - Create all tables

Revision ID: 001_initial
Revises:
Create Date: 2026-04-19

"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "001_initial"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # =============================================================================
    # users
    # =============================================================================
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("username", sa.String(length=50), nullable=False),
        sa.Column("phone", sa.String(length=20), nullable=True),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=True),
        sa.Column("role", sa.String(length=20), nullable=False, server_default="operator"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="1"),
        sa.Column("is_first_login", sa.Boolean(), nullable=False, server_default="1"),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("username"),
        sa.UniqueConstraint("phone"),
    )

    # =============================================================================
    # videos
    # =============================================================================
    op.create_table(
        "videos",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("code", sa.String(length=50), nullable=False),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("file_path", sa.String(length=500), nullable=True),
        sa.Column("cover_image", sa.String(length=500), nullable=True),
        sa.Column("duration", sa.Float(), nullable=True),
        sa.Column("file_size", sa.BigInteger(), nullable=True),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="uploading"),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("created_by", sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("code"),
    )

    # =============================================================================
    # cultural_products
    # =============================================================================
    op.create_table(
        "cultural_products",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("code", sa.String(length=50), nullable=False),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("cover_image", sa.String(length=500), nullable=True),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="active"),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("code"),
    )

    # =============================================================================
    # nfc_tags
    # =============================================================================
    op.create_table(
        "nfc_tags",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("url_code", sa.String(length=100), nullable=False),
        sa.Column("video_id", sa.Integer(), nullable=True),
        sa.Column("cultural_product_id", sa.Integer(), nullable=True),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="active"),
        sa.Column("approval_status", sa.String(length=20), nullable=False, server_default="pending"),
        sa.Column("click_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("created_by", sa.Integer(), nullable=True),
        sa.Column("approved_by", sa.Integer(), nullable=True),
        sa.Column("approved_at", sa.Date(), nullable=True),
        sa.ForeignKeyConstraint(["video_id"], ["videos.id"]),
        sa.ForeignKeyConstraint(["cultural_product_id"], ["cultural_products.id"]),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"]),
        sa.ForeignKeyConstraint(["approved_by"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("url_code"),
    )

    # =============================================================================
    # tag_clicks
    # =============================================================================
    op.create_table(
        "tag_clicks",
        sa.Column("id", sa.BigInteger(), nullable=False),
        sa.Column("tag_id", sa.Integer(), nullable=True),
        sa.Column("click_time", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("ip_address", sa.String(length=50), nullable=True),
        sa.Column("user_agent", sa.String(length=500), nullable=True),
        sa.Column("referer", sa.String(length=500), nullable=True),
        sa.ForeignKeyConstraint(["tag_id"], ["nfc_tags.id"]),
        sa.PrimaryKeyConstraint("id"),
    )

    # =============================================================================
    # sessions
    # =============================================================================
    op.create_table(
        "sessions",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=True),
        sa.Column("token", sa.String(length=500), nullable=False),
        sa.Column("device_info", sa.String(length=500), nullable=True),
        sa.Column("ip_address", sa.String(length=50), nullable=True),
        sa.Column("last_active", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("expires_at", sa.DateTime(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="1"),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("token"),
    )

    # =============================================================================
    # videos_cultural_products (many-to-many)
    # =============================================================================
    op.create_table(
        "videos_cultural_products",
        sa.Column("video_id", sa.Integer(), nullable=False),
        sa.Column("cultural_product_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["video_id"], ["videos.id"]),
        sa.ForeignKeyConstraint(["cultural_product_id"], ["cultural_products.id"]),
        sa.PrimaryKeyConstraint("video_id", "cultural_product_id"),
    )

    # =============================================================================
    # Indexes
    # =============================================================================
    op.create_index("ix_nfc_tags_url_code", "nfc_tags", ["url_code"])
    op.create_index("ix_tag_clicks_tag_id", "tag_clicks", ["tag_id"])
    op.create_index("ix_tag_clicks_click_time", "tag_clicks", ["click_time"])
    op.create_index("ix_sessions_user_id", "sessions", ["user_id"])
    op.create_index("ix_videos_status", "videos", ["status"])


def downgrade() -> None:
    op.drop_table("videos_cultural_products")
    op.drop_table("sessions")
    op.drop_table("tag_clicks")
    op.drop_table("nfc_tags")
    op.drop_table("cultural_products")
    op.drop_table("videos")
    op.drop_table("users")
