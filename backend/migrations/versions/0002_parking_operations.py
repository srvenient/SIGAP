"""Operación del parqueadero según la documentación V2.1.

Revision ID: 0002
Revises: 0001
"""
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB

from core.immutable import (
    CREATE_FUNCTION,
    DROP_FUNCTION,
    IMMUTABLE_TABLES,
    create_trigger_statements,
    drop_trigger_statements,
)

revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None

DEFAULT_LOT_ID = "00000000-0000-4000-8000-000000000001"
_TZ = sa.DateTime(timezone=True)
_MONEY = sa.Numeric(12, 2)


def _lot_fk() -> sa.Column:
    return sa.Column("parking_lot_id", sa.Uuid(), sa.ForeignKey("parking_lots.id"), nullable=False)


def _upgrade_transactions() -> None:
    op.execute(f"UPDATE transactions SET parking_lot_id = '{DEFAULT_LOT_ID}' WHERE parking_lot_id IS NULL")
    op.alter_column("transactions", "parking_lot_id", nullable=False)
    op.create_foreign_key(
        "fk_transactions_parking_lot", "transactions", "parking_lots", ["parking_lot_id"], ["id"]
    )
    op.create_index("ix_transactions_parking_lot_id", "transactions", ["parking_lot_id"])

    op.alter_column(
        "transactions", "total_amount", type_=_MONEY, postgresql_using="total_amount::numeric(12,2)"
    )
    op.add_column("transactions", sa.Column("entry_gate_opened_at", _TZ, nullable=True))
    op.add_column("transactions", sa.Column("billed_minutes", sa.Integer(), nullable=True))
    op.add_column("transactions", sa.Column("tariff_snapshot", JSONB(), nullable=True))
    op.add_column("transactions", sa.Column("paid_at", _TZ, nullable=True))
    op.add_column("transactions", sa.Column("manual_reason", sa.String(300), nullable=True))

    # Los vehículos ya registrados pasaron por la talanquera
    op.execute("UPDATE transactions SET entry_gate_opened_at = entry_time")
    op.execute("UPDATE transactions SET paid_at = updated_at WHERE status IN ('PAID', 'COMPLETED')")
    # El estado "procesando" dejó de existir: el documento exige permanecer en Ingresado
    op.execute("UPDATE transactions SET status = 'ENTERED' WHERE status = 'PROCESSING_PAYMENT'")

    op.create_index("ix_transactions_status", "transactions", ["status"])
    op.create_index("ix_transactions_entry_time", "transactions", ["entry_time"])
    op.create_index("ix_transactions_paid_at", "transactions", ["paid_at"])
    op.create_index(
        "uq_transactions_active_plate",
        "transactions",
        ["plate"],
        unique=True,
        postgresql_where=sa.text("status IN ('ENTERED', 'PAID')"),
    )


def upgrade() -> None:
    op.create_table(
        "parking_lots",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("name", sa.String(120), nullable=False),
        sa.Column("address", sa.String(200), nullable=True),
        sa.Column("capacity", sa.Integer(), nullable=False),
        sa.Column("gate_open_seconds", sa.Integer(), nullable=False),
        sa.Column("created_at", _TZ, nullable=False),
        sa.Column("updated_at", _TZ, nullable=False),
    )
    op.execute(
        "INSERT INTO parking_lots (id, name, capacity, gate_open_seconds, created_at, updated_at) "
        f"VALUES ('{DEFAULT_LOT_ID}', 'Sede principal', 50, 3, now(), now())"
    )

    _upgrade_transactions()

    op.create_index("ix_users_username", "users", ["username"], unique=True)

    op.create_table(
        "audit_logs",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("actor_user_id", sa.Uuid(), nullable=True),
        sa.Column("actor_label", sa.String(80), nullable=False),
        sa.Column("action", sa.String(40), nullable=False),
        sa.Column("entity_type", sa.String(40), nullable=False),
        sa.Column("entity_id", sa.String(64), nullable=True),
        sa.Column("entity_label", sa.String(120), nullable=True),
        sa.Column("result", sa.String(10), nullable=False),
        sa.Column("detail", JSONB(), nullable=False),
        sa.Column("created_at", _TZ, nullable=False),
    )
    op.create_index("ix_audit_logs_actor_user_id", "audit_logs", ["actor_user_id"])
    op.create_index("ix_audit_logs_actor_label", "audit_logs", ["actor_label"])
    op.create_index("ix_audit_logs_action", "audit_logs", ["action"])
    op.create_index("ix_audit_logs_created_at", "audit_logs", ["created_at"])

    op.create_table(
        "tariffs",
        sa.Column("id", sa.Uuid(), primary_key=True),
        _lot_fk(),
        sa.Column("vehicle_type", sa.String(20), nullable=False),
        sa.Column("hourly_rate", _MONEY, nullable=False),
        sa.Column("fraction_rate", _MONEY, nullable=False),
        sa.Column("fraction_minutes", sa.Integer(), nullable=False),
        sa.Column("full_rate", _MONEY, nullable=False),
        sa.Column("full_rate_after_minutes", sa.Integer(), nullable=False),
        sa.Column("updated_at", _TZ, nullable=False),
        sa.UniqueConstraint("parking_lot_id", "vehicle_type", name="uq_tariff_lot_vehicle"),
    )
    op.create_index("ix_tariffs_parking_lot_id", "tariffs", ["parking_lot_id"])

    op.create_table(
        "tariff_history",
        sa.Column("id", sa.Uuid(), primary_key=True),
        _lot_fk(),
        sa.Column("vehicle_type", sa.String(20), nullable=False),
        sa.Column("previous_config", JSONB(), nullable=False),
        sa.Column("new_config", JSONB(), nullable=False),
        sa.Column("changed_by_id", sa.Uuid(), nullable=True),
        sa.Column("changed_by_username", sa.String(80), nullable=False),
        sa.Column("changed_at", _TZ, nullable=False),
    )
    op.create_index("ix_tariff_history_parking_lot_id", "tariff_history", ["parking_lot_id"])
    op.create_index("ix_tariff_history_vehicle_type", "tariff_history", ["vehicle_type"])
    op.create_index("ix_tariff_history_changed_at", "tariff_history", ["changed_at"])

    op.create_table(
        "payment_attempts",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("transaction_id", sa.Uuid(), sa.ForeignKey("transactions.id"), nullable=False),
        sa.Column("reference", sa.String(64), nullable=False),
        sa.Column("gateway", sa.String(30), nullable=False),
        sa.Column("method", sa.String(30), nullable=False),
        sa.Column("amount", _MONEY, nullable=False),
        sa.Column("billed_minutes", sa.Integer(), nullable=False),
        sa.Column("tariff_snapshot", JSONB(), nullable=False),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("failure_reason", sa.String(200), nullable=True),
        sa.Column("created_at", _TZ, nullable=False),
        sa.Column("resolved_at", _TZ, nullable=True),
    )
    op.create_index("ix_payment_attempts_transaction_id", "payment_attempts", ["transaction_id"])
    op.create_index("ix_payment_attempts_reference", "payment_attempts", ["reference"], unique=True)
    op.create_index("ix_payment_attempts_status", "payment_attempts", ["status"])
    op.create_index("ix_payment_attempts_created_at", "payment_attempts", ["created_at"])

    op.create_table(
        "devices",
        sa.Column("id", sa.Uuid(), primary_key=True),
        _lot_fk(),
        sa.Column("code", sa.String(30), nullable=False),
        sa.Column("kind", sa.String(20), nullable=False),
        sa.Column("name", sa.String(80), nullable=False),
        sa.Column("reported_status", sa.String(20), nullable=False),
        sa.Column("last_error", sa.String(300), nullable=True),
        sa.Column("last_report_at", _TZ, nullable=True),
        sa.Column("last_seen_at", _TZ, nullable=True),
        sa.UniqueConstraint("parking_lot_id", "code", name="uq_device_lot_code"),
    )
    op.create_index("ix_devices_parking_lot_id", "devices", ["parking_lot_id"])

    op.create_table(
        "technical_events",
        sa.Column("id", sa.Uuid(), primary_key=True),
        _lot_fk(),
        sa.Column("device_id", sa.Uuid(), sa.ForeignKey("devices.id"), nullable=True),
        sa.Column("component", sa.String(80), nullable=False),
        sa.Column("error_code", sa.String(40), nullable=False),
        sa.Column("description", sa.String(500), nullable=False),
        sa.Column("transaction_id", sa.Uuid(), sa.ForeignKey("transactions.id"), nullable=True),
        sa.Column("created_at", _TZ, nullable=False),
    )
    op.create_index("ix_technical_events_parking_lot_id", "technical_events", ["parking_lot_id"])
    op.create_index("ix_technical_events_device_id", "technical_events", ["device_id"])
    op.create_index("ix_technical_events_error_code", "technical_events", ["error_code"])
    op.create_index("ix_technical_events_created_at", "technical_events", ["created_at"])

    op.create_table(
        "gate_commands",
        sa.Column("id", sa.Uuid(), primary_key=True),
        _lot_fk(),
        sa.Column("gate", sa.String(10), nullable=False),
        sa.Column("transaction_id", sa.Uuid(), sa.ForeignKey("transactions.id"), nullable=True),
        sa.Column("reason", sa.String(300), nullable=False),
        sa.Column("requested_by_id", sa.Uuid(), nullable=True),
        sa.Column("requested_by_username", sa.String(80), nullable=False),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("error", sa.String(300), nullable=True),
        sa.Column("created_at", _TZ, nullable=False),
        sa.Column("completed_at", _TZ, nullable=True),
    )
    op.create_index("ix_gate_commands_parking_lot_id", "gate_commands", ["parking_lot_id"])
    op.create_index("ix_gate_commands_status", "gate_commands", ["status"])
    op.create_index("ix_gate_commands_created_at", "gate_commands", ["created_at"])

    op.create_table(
        "gate_displays",
        sa.Column("id", sa.Uuid(), primary_key=True),
        _lot_fk(),
        sa.Column("gate", sa.String(10), nullable=False),
        sa.Column("state", sa.String(20), nullable=False),
        sa.Column("message", sa.String(120), nullable=False),
        sa.Column("plate", sa.String(10), nullable=True),
        sa.Column("expires_at", _TZ, nullable=True),
        sa.UniqueConstraint("parking_lot_id", "gate", name="uq_display_lot_gate"),
    )
    op.create_index("ix_gate_displays_parking_lot_id", "gate_displays", ["parking_lot_id"])

    op.create_table(
        "operation_alerts",
        sa.Column("id", sa.Uuid(), primary_key=True),
        _lot_fk(),
        sa.Column("gate", sa.String(10), nullable=False),
        sa.Column("alert_type", sa.String(30), nullable=False),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("plate_read", sa.String(10), nullable=True),
        sa.Column("message", sa.String(200), nullable=False),
        sa.Column("has_snapshot", sa.Boolean(), nullable=False),
        sa.Column("transaction_id", sa.Uuid(), sa.ForeignKey("transactions.id"), nullable=True),
        sa.Column("resolved_by_id", sa.Uuid(), nullable=True),
        sa.Column("resolved_by_username", sa.String(80), nullable=True),
        sa.Column("resolution_note", sa.String(300), nullable=True),
        sa.Column("created_at", _TZ, nullable=False),
        sa.Column("resolved_at", _TZ, nullable=True),
    )
    op.create_index("ix_operation_alerts_parking_lot_id", "operation_alerts", ["parking_lot_id"])
    op.create_index("ix_operation_alerts_status", "operation_alerts", ["status"])
    op.create_index("ix_operation_alerts_plate_read", "operation_alerts", ["plate_read"])
    op.create_index("ix_operation_alerts_created_at", "operation_alerts", ["created_at"])

    op.create_table(
        "alert_snapshots",
        sa.Column("alert_id", sa.Uuid(), sa.ForeignKey("operation_alerts.id"), primary_key=True),
        sa.Column("image", sa.LargeBinary(), nullable=False),
    )

    op.create_table(
        "tickets",
        sa.Column("id", sa.Uuid(), primary_key=True),
        _lot_fk(),
        sa.Column("origin", sa.String(20), nullable=False),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("assigned_role", sa.String(20), nullable=False),
        sa.Column("component", sa.String(80), nullable=False),
        sa.Column("error_code", sa.String(40), nullable=True),
        sa.Column("description", sa.String(1000), nullable=False),
        sa.Column("transaction_id", sa.Uuid(), sa.ForeignKey("transactions.id"), nullable=True),
        sa.Column("technical_event_id", sa.Uuid(), sa.ForeignKey("technical_events.id"), nullable=True),
        sa.Column("created_by_id", sa.Uuid(), nullable=True),
        sa.Column("created_by_username", sa.String(80), nullable=False),
        sa.Column("assignee_id", sa.Uuid(), nullable=True),
        sa.Column("assignee_username", sa.String(80), nullable=True),
        sa.Column("diagnosis", sa.String(2000), nullable=True),
        sa.Column("actions_taken", sa.String(2000), nullable=True),
        sa.Column("result", sa.String(2000), nullable=True),
        sa.Column("created_at", _TZ, nullable=False),
        sa.Column("updated_at", _TZ, nullable=False),
    )
    op.create_index("ix_tickets_parking_lot_id", "tickets", ["parking_lot_id"])
    op.create_index("ix_tickets_status", "tickets", ["status"])
    op.create_index("ix_tickets_component", "tickets", ["component"])
    op.create_index("ix_tickets_created_by_id", "tickets", ["created_by_id"])
    op.create_index("ix_tickets_created_at", "tickets", ["created_at"])

    op.create_table(
        "ticket_history",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("ticket_id", sa.Uuid(), sa.ForeignKey("tickets.id"), nullable=False),
        sa.Column("from_status", sa.String(20), nullable=True),
        sa.Column("to_status", sa.String(20), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=True),
        sa.Column("username", sa.String(80), nullable=False),
        sa.Column("note", sa.String(300), nullable=True),
        sa.Column("created_at", _TZ, nullable=False),
    )
    op.create_index("ix_ticket_history_ticket_id", "ticket_history", ["ticket_id"])

    op.execute(CREATE_FUNCTION)
    for table in IMMUTABLE_TABLES:
        for statement in create_trigger_statements(table):
            op.execute(statement)


def downgrade() -> None:
    for table in IMMUTABLE_TABLES:
        for statement in drop_trigger_statements(table):
            op.execute(statement)
    op.execute(DROP_FUNCTION)

    for table in (
            "ticket_history", "tickets", "alert_snapshots", "operation_alerts", "gate_displays",
            "gate_commands", "technical_events", "devices", "payment_attempts", "tariff_history",
            "tariffs", "audit_logs",
    ):
        op.drop_table(table)

    op.drop_index("ix_users_username", table_name="users")
    for index in (
            "uq_transactions_active_plate", "ix_transactions_paid_at", "ix_transactions_entry_time",
            "ix_transactions_status", "ix_transactions_parking_lot_id",
    ):
        op.drop_index(index, table_name="transactions")
    for column in ("manual_reason", "paid_at", "tariff_snapshot", "billed_minutes", "entry_gate_opened_at"):
        op.drop_column("transactions", column)
    op.alter_column("transactions", "total_amount", type_=sa.Float())
    op.drop_constraint("fk_transactions_parking_lot", "transactions", type_="foreignkey")
    op.alter_column("transactions", "parking_lot_id", nullable=True)
    op.drop_table("parking_lots")
