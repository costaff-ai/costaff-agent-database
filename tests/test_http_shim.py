"""Tests for agent/tools/_http.py — the plain-httpx shim that fan-outs
to manager-core MCP via POST <base>/api/tool/<name>.

The shim is deliberately tiny (no MCP client, no anyio task group) to
sidestep the ADK cancel-scope race. These tests pin that contract:

- Correct URL construction (no double slashes, /api/tool/<tool>)
- JSON body carries the kwargs verbatim
- Authorization header set when MCP_SECRET_KEY is configured
- Non-200 responses return a friendly '[ERROR] ...' string, not raise
- Transport errors (connection refused etc.) caught and stringified
- 200 response with JSON 'result' field returns that value
"""
from __future__ import annotations

from unittest.mock import MagicMock

from tools._http import call_shim
from tests.conftest import make_response


def test_call_shim_posts_to_correct_url(mock_httpx):
    mock_httpx.post.return_value = make_response(200, {"result": "ok"})
    call_shim("http://core:8081", "send_message_now", channel="tg", recipient="x")
    args, kwargs = mock_httpx.post.call_args
    assert args[0] == "http://core:8081/api/tool/send_message_now"


def test_call_shim_strips_trailing_slash_from_base_url(mock_httpx):
    mock_httpx.post.return_value = make_response(200, {"result": "ok"})
    call_shim("http://core:8081/", "send_message_now")
    assert mock_httpx.post.call_args[0][0] == "http://core:8081/api/tool/send_message_now"


def test_call_shim_passes_kwargs_as_json_body(mock_httpx):
    mock_httpx.post.return_value = make_response(200, {"result": "ok"})
    call_shim("http://core:8081", "list_data_files", path="/app/data", pattern="*.csv")
    _, kwargs = mock_httpx.post.call_args
    assert kwargs["json"] == {"path": "/app/data", "pattern": "*.csv"}


def test_call_shim_returns_result_field_on_200(mock_httpx):
    mock_httpx.post.return_value = make_response(200, {"result": "12 files found"})
    out = call_shim("http://core:8081", "list_data_files", path="/app/data")
    assert out == "12 files found"


def test_call_shim_returns_friendly_error_on_non_200(mock_httpx):
    mock_httpx.post.return_value = make_response(
        500, json_body={"error": "internal exploded"}
    )
    out = call_shim("http://core:8081", "send_message_now", channel="x", recipient="y")
    assert out.startswith("[ERROR]")
    assert "500" in out
    assert "internal exploded" in out


def test_call_shim_handles_non_json_error_body(mock_httpx):
    mock_httpx.post.return_value = make_response(404, text="<html>not found</html>")
    out = call_shim("http://core:8081", "ghost_tool")
    assert out.startswith("[ERROR]")
    assert "404" in out
    assert "not found" in out


def test_call_shim_catches_transport_errors(mock_httpx):
    """Connection refused / DNS failure must surface as a string, not
    propagate an exception that would crash the agent's tool loop."""
    mock_httpx.post.side_effect = Exception("connection refused")
    out = call_shim("http://core:8081", "send_message_now")
    assert out.startswith("[ERROR]")
    assert "could not reach" in out.lower()
    assert "connection refused" in out


def test_call_shim_returns_text_when_response_not_json(mock_httpx):
    """Some endpoints might return plain text on 200; fall back to .text."""
    r = MagicMock()
    r.status_code = 200
    r.json = MagicMock(side_effect=ValueError("not json"))
    r.text = "raw text response"
    mock_httpx.post.return_value = r
    out = call_shim("http://core:8081", "weird_tool")
    assert out == "raw text response"


def test_call_shim_sets_authorization_when_secret_configured(monkeypatch, mock_httpx):
    """If MCP_SECRET_KEY is set at module-import time, every request
    carries an `Authorization: Bearer <secret>` header. We can't easily
    reload the module here, so we patch the module-level _SECRET and
    re-invoke."""
    import tools._http as _http

    monkeypatch.setattr(_http, "_SECRET", "super-secret-token")
    mock_httpx.post.return_value = make_response(200, {"result": "ok"})
    call_shim("http://core:8081", "send_message_now")
    _, kwargs = mock_httpx.post.call_args
    assert kwargs["headers"]["Authorization"] == "Bearer super-secret-token"


def test_call_shim_omits_authorization_when_secret_empty(monkeypatch, mock_httpx):
    import tools._http as _http

    monkeypatch.setattr(_http, "_SECRET", "")
    mock_httpx.post.return_value = make_response(200, {"result": "ok"})
    call_shim("http://core:8081", "send_message_now")
    _, kwargs = mock_httpx.post.call_args
    assert "Authorization" not in kwargs["headers"]
