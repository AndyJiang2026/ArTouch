"""Add nfc_tags_secure and verification_logs tables.

Revision ID: 008
Revises: 007
Create Date: 2026-04-22

"""
from alembic import op
import sqlalchemy as sa


revision = "008"
down_revision = "007"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # NfcTagSecure table
    op.create_table(
        "nfc_tags_secure",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("uid", sa.String(length=16), nullable=False),
        sa.Column("nfc_tag_id", sa.Integer(), nullable=True),
        sa.Column("key_material", sa.Text(), nullable=False),
        sa.Column("signature", sa.Text(), nullable=False),
        sa.Column("counter", sa.Integer(), nullable=False),
        sa.Column("master_key_id", sa.String(length=50), nullable=True),
        sa.Column("product_name", sa.String(length=200), nullable=True),
        sa.Column("registered_at", sa.DateTime(), nullable=True),
        sa.Column("last_verified_at", sa.DateTime(), nullable=True),
        sa.Column("is_active", sa.Integer(), nullable=True, default=1),
        sa.Column("note", sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(["nfc_tag_id"], ["nfc_tags.id"], ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_nfc_tags_secure_id"), "nfc_tags_secure", ["id"], unique=False)
    op.create_index(op.f("ix_nfc_tags_secure_uid"), "nfc_tags_secure", ["uid"], unique=True)

    # VerificationLog table
    op.create_table(
        "verification_logs",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("tag_secure_id", sa.Integer(), nullable=False),
        sa.Column("uid", sa.String(length=16), nullable=False),
        sa.Column("result", sa.String(length=20), nullable=False),
        sa.Column("detail", sa.Text(), nullable=True),
        sa.Column("client_ip", sa.String(length=50), nullable=True),
        sa.Column("user_agent", sa.Text(), nullable=True),
        sa.Column("submitted_signature", sa.Text(), nullable=True),
        sa.Column("submitted_counter", sa.Integer(), nullable=True),
        sa.Column("is_success", sa.Integer(), nullable=True, default=0),
        sa.Column("verified_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["tag_secure_id"], ["nfc_tags_secure.id"], ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_verification_logs_id"), "verification_logs", ["id"], unique=False)
    op.create_index(op.f("ix_verification_logs_tag_secure_id"), "verification_logs", ["tag_secure_id"], unique=False)
    op.create_index(op.f("ix_verification_logs_uid"), "verification_logs", ["uid"], unique=False)
    op.create_index(op.f("ix_verification_logs_verified_at"), "verification_logs", ["verified_at"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_verification_logs_verified_at"), table_name="verification_logs")
    op.drop_index(op.f("ix_verification_logs_uid"), table_name="verification_logs")
    op.drop_index(op.f("ix_verification_logs_tag_secure_id"), table_name="verification_logs")
    op.drop_index(op.f("ix_verification_logs_id"), table_name="verification_logs")
    op.drop_table("verification_logs")

    op.drop_index(op.f("ix_nfc_tags_secure_uid"), table_name="nfc_tags_secure")
    op.drop_index(op.f("ix_nfc_tags_secure_id"), table_name="nfc_tags_secure")
    op.drop_table("nfc_tags_secure")
