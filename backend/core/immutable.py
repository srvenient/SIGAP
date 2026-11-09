"""Triggers de Postgres que impiden alterar los registros históricos (HU-14, HU-25, HU-28).

Lo usan la migración y las pruebas, para que ambas instalen exactamente los mismos triggers.
"""

IMMUTABLE_TABLES = ("audit_logs", "tariff_history", "ticket_history")

CREATE_FUNCTION = """
CREATE OR REPLACE FUNCTION sigap_reject_change() RETURNS trigger AS $$
BEGIN
    RAISE EXCEPTION 'Los registros de % son inmutables', TG_TABLE_NAME;
END;
$$ LANGUAGE plpgsql;
"""

DROP_FUNCTION = "DROP FUNCTION IF EXISTS sigap_reject_change();"


def create_trigger_statements(table: str) -> list[str]:
    return [
        f"CREATE TRIGGER trg_{table}_immutable BEFORE UPDATE OR DELETE ON {table} "
        "FOR EACH ROW EXECUTE FUNCTION sigap_reject_change();",
        f"CREATE TRIGGER trg_{table}_no_truncate BEFORE TRUNCATE ON {table} "
        "FOR EACH STATEMENT EXECUTE FUNCTION sigap_reject_change();",
    ]


def drop_trigger_statements(table: str) -> list[str]:
    return [
        f"DROP TRIGGER IF EXISTS trg_{table}_immutable ON {table};",
        f"DROP TRIGGER IF EXISTS trg_{table}_no_truncate ON {table};",
    ]
