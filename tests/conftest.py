"""pytest fixtures for the database agent test suite.

Two concerns this conftest covers:

1. The agent-side `tools/_http` shim talks to manager core MCP via
   plain httpx. We mock httpx so tests never hit a real network.
   (Mirrors the template repo conventions.)

2. The MCP-side `tools/db_operations` actually executes SQL against
   whatever URL `DATABASE_CONFIG` env var resolves to. We seed a
   real file-based sqlite under `tmp_path` and point the env var at
   it — full integration coverage with zero external services.

Path note: both `agent/tools/` and `mcp/tools/` exist under their own
sys.path roots, so a bare `import tools.X` is ambiguous. The MCP-side
module is loaded explicitly by file path and re-exported under a
disambiguating module name (`db_operations`) below.
"""
from __future__ import annotations

import importlib.util
import json
import os
import sys
from pathlib import Path
from unittest.mock import MagicMock

import pytest
from sqlalchemy import create_engine, text


# ---------- Load mcp/tools/db_operations explicitly via file path ----
# Bypasses the `tools/` namespace collision with agent/tools/.
_DB_OPS_PATH = Path(__file__).resolve().parent.parent / "mcp" / "tools" / "db_operations.py"
_spec = importlib.util.spec_from_file_location("db_operations", _DB_OPS_PATH)
db_operations = importlib.util.module_from_spec(_spec)
sys.modules["db_operations"] = db_operations
_spec.loader.exec_module(db_operations)


def make_response(status: int, json_body=None, *, text: str = ""):
    """Build a MagicMock that quacks like an httpx.Response."""
    r = MagicMock()
    r.status_code = status
    if json_body is not None:
        r.json = MagicMock(return_value=json_body)
        r.text = json.dumps(json_body)
    else:
        r.json = MagicMock(side_effect=ValueError("not JSON"))
        r.text = text
    return r


@pytest.fixture
def mock_httpx(mocker):
    """Patch httpx inside tools._http with a mock whose .post returns
    whatever the test stages via mock.return_value."""
    import tools._http as _http

    fake_httpx = MagicMock()
    fake_httpx.post = MagicMock()
    mocker.patch.object(_http, "httpx", new=fake_httpx)
    return fake_httpx


@pytest.fixture
def seeded_sqlite(tmp_path):
    """Create a file-based sqlite DB seeded with one users + one orders
    table; return its URL so tests can plug it into DATABASE_CONFIG."""
    db_path = tmp_path / "test.db"
    url = f"sqlite:///{db_path}"
    engine = create_engine(url)
    with engine.begin() as conn:
        conn.execute(text(
            "CREATE TABLE users (id INTEGER PRIMARY KEY, name TEXT, email TEXT)"
        ))
        conn.execute(text(
            "INSERT INTO users (id, name, email) VALUES "
            "(1, 'Alice', 'alice@example.com'), "
            "(2, 'Bob', 'bob@example.com'), "
            "(3, 'Carol', 'carol@example.com'), "
            "(4, 'Dave', 'dave@example.com')"
        ))
        conn.execute(text(
            "CREATE TABLE orders (id INTEGER PRIMARY KEY, user_id INTEGER, total REAL)"
        ))
        conn.execute(text(
            "INSERT INTO orders (id, user_id, total) VALUES "
            "(1, 1, 99.50), (2, 1, 12.30), (3, 2, 250.00)"
        ))
    return url


@pytest.fixture
def db_config_env(seeded_sqlite, monkeypatch, tmp_path):
    """Set DATABASE_CONFIG to point at the seeded sqlite + the
    workspace dirs at temp paths so query(output_filename=...) writes
    where we can inspect."""
    config = {
        "primary": {
            "type": "sqlite",
            "url": seeded_sqlite,
            "desc": "Primary test database",
        },
        "secondary": {
            "type": "sqlite",
            "url": f"sqlite:///{tmp_path}/secondary.db",
            "desc": "Empty secondary database",
        },
    }
    monkeypatch.setenv("DATABASE_CONFIG", json.dumps(config))
    monkeypatch.setenv("WORKSPACE_DIR", str(tmp_path / "workspace"))
    monkeypatch.setenv("COSTAFF_SHARED_DIR_DATABASE", str(tmp_path / "shared"))
    return config
