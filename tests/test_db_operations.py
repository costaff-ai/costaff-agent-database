"""Tests for mcp/tools/db_operations.py — the 4 native MCP tools the
database agent exposes:

  - get_connected_databases()
  - inspect_database(db_alias)
  - inspect_table(db_alias, table_name)
  - query(db_alias, sql, output_filename=None)

Strategy: drive the real sqlalchemy code against a file-based sqlite
seeded by the `seeded_sqlite` fixture in conftest. No mocking of the
DB layer — the tests exercise the actual SQL path. Only env vars are
swapped (via monkeypatch).
"""
from __future__ import annotations

import json
import os
from pathlib import Path

import pytest

# Loaded by conftest under the unambiguous name `db_operations` —
# both `agent/tools/` and `mcp/tools/` sit on pythonpath, so a bare
# `import tools.db_operations` is ambiguous.
from db_operations import (
    _get_db_config,
    _shared_workspace,
    _workspace,
    get_connected_databases,
    inspect_database,
    inspect_table,
    query,
)


# ---------------------------------------- _get_db_config / workspaces

def test_get_db_config_returns_dict_for_valid_json(monkeypatch):
    monkeypatch.setenv("DATABASE_CONFIG", '{"primary": {"url": "sqlite:///:memory:"}}')
    cfg = _get_db_config()
    assert cfg == {"primary": {"url": "sqlite:///:memory:"}}


def test_get_db_config_empty_string_returns_empty_dict(monkeypatch):
    monkeypatch.setenv("DATABASE_CONFIG", "")
    assert _get_db_config() == {}


def test_get_db_config_malformed_json_returns_empty_dict(monkeypatch):
    """A garbled env var should never crash the tool; the tool returns
    a friendly 'no databases configured' instead. The error-swallow is
    intentional — operators sometimes paste config with stray commas."""
    monkeypatch.setenv("DATABASE_CONFIG", "{not valid json")
    assert _get_db_config() == {}


def test_get_db_config_unset_returns_empty_dict(monkeypatch):
    monkeypatch.delenv("DATABASE_CONFIG", raising=False)
    assert _get_db_config() == {}


def test_workspace_falls_back_to_default(monkeypatch):
    monkeypatch.delenv("WORKSPACE_DIR", raising=False)
    assert _workspace() == "/app/data/costaff-agent-database"


def test_shared_workspace_falls_back_to_default(monkeypatch):
    monkeypatch.delenv("COSTAFF_SHARED_DIR_DATABASE", raising=False)
    assert _shared_workspace() == "/app/data/shared/costaff-agent-database"


# ---------------------------------------- get_connected_databases

def test_get_connected_databases_lists_all_with_descriptions(db_config_env):
    result = get_connected_databases()
    data = json.loads(result)
    aliases = {row["alias"] for row in data}
    assert aliases == {"primary", "secondary"}
    primary = next(r for r in data if r["alias"] == "primary")
    assert primary["type"] == "sqlite"
    assert "Primary" in primary["description"]


def test_get_connected_databases_handles_missing_optional_fields(monkeypatch):
    """`type` and `desc` are optional in the config; missing values fall
    back to friendly defaults instead of KeyError."""
    monkeypatch.setenv("DATABASE_CONFIG", '{"x": {"url": "sqlite:///:memory:"}}')
    result = get_connected_databases()
    row = json.loads(result)[0]
    assert row["alias"] == "x"
    assert row["type"] == "unknown"
    assert row["description"] == "No description"


def test_get_connected_databases_no_config_returns_helpful_message(monkeypatch):
    monkeypatch.delenv("DATABASE_CONFIG", raising=False)
    result = get_connected_databases()
    assert "No databases configured" in result
    assert "DATABASE_CONFIG" in result


# ---------------------------------------- inspect_database

def test_inspect_database_lists_tables(db_config_env):
    result = inspect_database("primary")
    data = json.loads(result)
    assert data["database"] == "primary"
    assert set(data["tables"]) == {"users", "orders"}


def test_inspect_database_unknown_alias_returns_error_string(db_config_env):
    result = inspect_database("ghost")
    assert "Error" in result
    assert "ghost" in result


def test_inspect_database_unreachable_url_returns_error_string(monkeypatch):
    monkeypatch.setenv(
        "DATABASE_CONFIG",
        '{"broken": {"url": "postgresql://nouser:nopass@localhost:1/x"}}',
    )
    result = inspect_database("broken")
    # Either psycopg2 isn't installed (driver error) or the connection
    # refuses — both surface as "Error connecting to 'broken'".
    assert "Error" in result and "broken" in result


# ---------------------------------------- inspect_table

def test_inspect_table_returns_columns_and_sample_rows(db_config_env):
    result = inspect_table("primary", "users")
    data = json.loads(result)
    assert data["table"] == "users"
    col_names = {c["name"] for c in data["columns"]}
    assert col_names == {"id", "name", "email"}
    # 4 seeded users but the tool caps at LIMIT 3.
    assert len(data["sample_rows"]) == 3
    assert data["sample_rows"][0]["name"] == "Alice"


def test_inspect_table_rejects_unknown_table_without_running_sql(db_config_env):
    """SQL-injection guard: an injection-shaped table name must fail
    cleanly and the injected DDL must NOT execute. Whether the failure
    surfaces as the explicit `{"error": ...}` JSON branch (when
    inspector.get_columns happens to succeed but the post-check fails)
    or as an `Error inspecting table ...` string (when SQLAlchemy's
    inspector raises NoSuchTable first) doesn't matter for safety —
    what matters is that the injection's `DROP` did NOT execute."""
    result = inspect_table("primary", "users; DROP TABLE orders")
    assert "error" in result.lower() or "Error" in result
    # The injection target must NOT have been executed — verify orders
    # is still there afterward.
    orders_check = inspect_database("primary")
    assert "orders" in json.loads(orders_check)["tables"]


def test_inspect_table_unknown_db_alias(db_config_env):
    result = inspect_table("ghost", "users")
    assert "Error" in result and "ghost" in result


# ---------------------------------------- query

def test_query_returns_rows_under_100_inline(db_config_env):
    result = query("primary", "SELECT * FROM users ORDER BY id")
    data = json.loads(result)
    assert data["database"] == "primary"
    assert data["row_count"] == 4
    assert len(data["data"]) == 4
    assert data["data"][0]["name"] == "Alice"
    assert "first 100 rows" in data["note"].lower()


def test_query_caps_inline_response_at_100_rows(db_config_env, monkeypatch):
    """Verify the 100-row inline cap actually applies. Insert 150 rows
    into a scratch table, query SELECT *, expect data length 100 but
    row_count to reflect the true total."""
    from sqlalchemy import create_engine, text
    url = json.loads(os.environ["DATABASE_CONFIG"])["primary"]["url"]
    eng = create_engine(url)
    with eng.begin() as conn:
        conn.execute(text("CREATE TABLE big (id INTEGER PRIMARY KEY)"))
        for i in range(150):
            conn.execute(text(f"INSERT INTO big (id) VALUES ({i})"))
    result = query("primary", "SELECT * FROM big ORDER BY id")
    data = json.loads(result)
    assert data["row_count"] == 150
    assert len(data["data"]) == 100


def test_query_writes_csv_when_output_filename_given(db_config_env, tmp_path):
    out = "users_dump.csv"
    result = query("primary", "SELECT * FROM users", output_filename=out)
    assert "Success" in result
    # Path embedded in the success message must point to a real file.
    target = Path(os.environ["COSTAFF_SHARED_DIR_DATABASE"]) / out
    assert target.exists()
    content = target.read_text()
    assert "Alice" in content and "alice@example.com" in content
    assert content.startswith("id,name,email")


def test_query_unknown_alias_returns_error_string(db_config_env):
    result = query("ghost", "SELECT 1")
    assert "Error" in result and "ghost" in result


def test_query_sql_error_returns_error_string_not_raise(db_config_env):
    """Syntactically broken SQL should NOT raise; it surfaces as a
    friendly error string the agent can read back to the user."""
    result = query("primary", "NOT VALID SQL")
    assert "Error" in result
    # Should not have crashed the process.


def test_query_writes_csv_to_shared_workspace_creating_dir(db_config_env, tmp_path):
    """The shared workspace dir is created on demand — operators don't
    have to pre-create it."""
    shared = tmp_path / "shared"
    assert not shared.exists()  # ensure starting clean
    query("primary", "SELECT 1 AS x", output_filename="probe.csv")
    assert shared.exists()
    assert (shared / "probe.csv").exists()
