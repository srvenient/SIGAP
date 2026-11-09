"""Esquema existente antes de adoptar Alembic.

Las bases creadas con create_all se marcan directamente en esta revisión (ver scripts/prestart.py).

Revision ID: 0001
Revises:
"""
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def _timestamp(name: str, nullable: bool = True) -> sa.Column:
    return sa.Column(name, sa.DateTime(timezone=True), nullable=nullable)


def upgrade() -> None:
    op.create_table(
        "roles",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("description", sa.String(), nullable=True),
    )
    op.create_index("ix_roles_name", "roles", ["name"], unique=True)

    op.create_table(
        "users",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("username", sa.String(20), nullable=False),
        sa.Column("full_name", sa.String(80), nullable=True),
        sa.Column("email", sa.String(120), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("role_id", sa.Uuid(), sa.ForeignKey("roles.id"), nullable=True),
        sa.Column("hashed_password", sa.String(), nullable=False),
        sa.Column("must_change_password", sa.Boolean(), server_default=sa.false(), nullable=False),
        _timestamp("password_changed_at"),
        sa.Column("failed_login_attempts", sa.Integer(), server_default="0", nullable=False),
        _timestamp("locked_until"),
        _timestamp("last_login"),
        _timestamp("created_at", nullable=False),
        _timestamp("updated_at", nullable=False),
    )

    op.create_table(
        "refresh_tokens",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("user_id", sa.Uuid(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("family_id", sa.Uuid(), nullable=False),
        sa.Column("token_hash", sa.String(64), nullable=False),
        _timestamp("expires_at", nullable=False),
        _timestamp("absolute_expires_at", nullable=False),
        _timestamp("revoked_at"),
        _timestamp("created_at", nullable=False),
    )
    op.create_index("ix_refresh_tokens_user_id", "refresh_tokens", ["user_id"])
    op.create_index("ix_refresh_tokens_family_id", "refresh_tokens", ["family_id"])
    op.create_index("ix_refresh_tokens_token_hash", "refresh_tokens", ["token_hash"], unique=True)

    op.create_table(
        "transactions",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("plate", sa.String(10), nullable=False),
        sa.Column(
            "vehicle_type",
            postgresql.ENUM("CAR", "MOTORCYCLE", "UNKNOWN", name="vehicletype"),
            nullable=False,
        ),
        sa.Column(
            "status",
            postgresql.ENUM("ENTERED", "PAID", "PROCESSING_PAYMENT", "COMPLETED", name="transactionstatus"),
            nullable=False,
        ),
        sa.Column("parking_lot_id", sa.Uuid(), nullable=True),
        sa.Column("total_amount", sa.Float(), nullable=True),
        sa.Column("payment_method", sa.String(50), nullable=True),
        sa.Column("payment_reference", sa.String(100), nullable=True),
        sa.Column("manual_intervention", sa.Boolean(), nullable=False),
        _timestamp("entry_time", nullable=False),
        _timestamp("exit_time"),
        _timestamp("created_at", nullable=False),
        _timestamp("updated_at", nullable=False),
    )
    op.create_index("ix_transactions_plate", "transactions", ["plate"])


def downgrade() -> None:
    op.drop_table("transactions")
    op.execute("DROP TYPE IF EXISTS transactionstatus")
    op.execute("DROP TYPE IF EXISTS vehicletype")
    op.drop_table("refresh_tokens")
    op.drop_table("users")
    op.drop_table("roles")
