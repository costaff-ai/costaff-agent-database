"""Tests for agent/tools/costaff_api.py — the 4 manager-core wrappers
the database agent uses to talk back to the manager (`send_message_now`,
`add_task_comment`, `move_to_shared`, `list_data_files`).

Each wrapper is a thin call to `call_shim(BASE, tool_name, **kwargs)`.
Tests verify:
- Correct tool name dispatched
- Correct kwargs forwarded
- Correct return-value passthrough
"""
from __future__ import annotations

from unittest.mock import patch

from tools.costaff_api import (
    add_task_comment,
    list_data_files,
    load_costaff_api_tools,
    move_to_shared,
    send_message_now,
)


# ----------------------------------------------------- send_message_now

def test_send_message_now_dispatches_to_shim():
    with patch("tools.costaff_api.call_shim", return_value="sent") as m:
        out = send_message_now(
            channel="telegram",
            recipient="user-123",
            body="[Database] query complete",
            user_id="user-123",
            session_id="sess-abc",
        )
        assert out == "sent"
        args, kwargs = m.call_args
        assert args[1] == "send_message_now"
        assert kwargs["channel"] == "telegram"
        assert kwargs["recipient"] == "user-123"
        assert kwargs["body"] == "[Database] query complete"
        assert kwargs["user_id"] == "user-123"
        assert kwargs["session_id"] == "sess-abc"


def test_send_message_now_default_app_name():
    with patch("tools.costaff_api.call_shim", return_value="") as m:
        send_message_now(channel="tg", recipient="r")
        _, kwargs = m.call_args
        assert kwargs["app_name"] == "costaff_agent"


def test_send_message_now_passes_subject_when_provided():
    with patch("tools.costaff_api.call_shim", return_value="") as m:
        send_message_now(channel="email", recipient="a@b.com", subject="Hello")
        _, kwargs = m.call_args
        assert kwargs["subject"] == "Hello"


# ----------------------------------------------------- add_task_comment

def test_add_task_comment_dispatches_to_shim():
    with patch("tools.costaff_api.call_shim", return_value="added") as m:
        out = add_task_comment(
            task_id="task-1",
            user_id="u",
            author="database_agent",
            content="Query returned 150 rows",
            comment_type="result",
        )
        assert out == "added"
        args, kwargs = m.call_args
        assert args[1] == "add_task_comment"
        assert kwargs["task_id"] == "task-1"
        assert kwargs["author"] == "database_agent"
        assert kwargs["content"] == "Query returned 150 rows"
        assert kwargs["comment_type"] == "result"


def test_add_task_comment_default_comment_type():
    with patch("tools.costaff_api.call_shim", return_value="") as m:
        add_task_comment(task_id="t", user_id="u", author="user", content="hi")
        _, kwargs = m.call_args
        assert kwargs["comment_type"] == "note"


# ----------------------------------------------------- move_to_shared

def test_move_to_shared_dispatches_to_shim():
    with patch("tools.costaff_api.call_shim", return_value="moved") as m:
        out = move_to_shared("/app/data/foo.csv", overwrite=True)
        assert out == "moved"
        args, kwargs = m.call_args
        assert args[1] == "move_to_shared"
        assert kwargs["src_path"] == "/app/data/foo.csv"
        assert kwargs["overwrite"] is True


def test_move_to_shared_overwrite_defaults_false():
    with patch("tools.costaff_api.call_shim", return_value="") as m:
        move_to_shared("/app/data/x")
        _, kwargs = m.call_args
        assert kwargs["overwrite"] is False


# ----------------------------------------------------- list_data_files

def test_list_data_files_dispatches_to_shim():
    with patch("tools.costaff_api.call_shim", return_value="[1,2]") as m:
        out = list_data_files("/app/data/shared", pattern="*.csv")
        assert out == "[1,2]"
        args, kwargs = m.call_args
        assert args[1] == "list_data_files"
        assert kwargs["path"] == "/app/data/shared"
        assert kwargs["pattern"] == "*.csv"


def test_list_data_files_pattern_defaults_none():
    with patch("tools.costaff_api.call_shim", return_value="") as m:
        list_data_files("/app/data")
        _, kwargs = m.call_args
        assert kwargs["pattern"] is None


# ----------------------------------------------------- load_costaff_api_tools

def test_load_costaff_api_tools_returns_four_callables():
    tools = load_costaff_api_tools()
    assert len(tools) == 4
    names = {t.__name__ for t in tools}
    assert names == {"send_message_now", "add_task_comment", "move_to_shared", "list_data_files"}


def test_load_costaff_api_tools_returns_actual_function_objects():
    """Each entry must be callable so ADK can register it as a tool."""
    for t in load_costaff_api_tools():
        assert callable(t)
