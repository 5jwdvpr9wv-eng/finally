"""Tests for chat_messages repository functions."""

import pytest

from app.db import get_recent_chat_messages, save_chat_message


class TestChatMessages:
    def test_save_user_message(self, temp_db):
        msg = save_chat_message("user", "Buy 5 AAPL")
        assert msg.role == "user"
        assert msg.content == "Buy 5 AAPL"
        assert msg.actions is None
        assert msg.id
        assert msg.created_at

    def test_save_assistant_with_actions(self, temp_db):
        actions = {"trades": [{"ticker": "AAPL", "side": "buy", "quantity": 5}]}
        msg = save_chat_message("assistant", "Done", actions=actions)
        assert msg.actions == actions

    def test_actions_roundtrip_through_db(self, temp_db):
        actions = {
            "trades": [{"ticker": "AAPL", "side": "buy", "quantity": 5}],
            "watchlist_changes": [{"ticker": "PYPL", "action": "add"}],
        }
        save_chat_message("assistant", "Executed", actions=actions)
        loaded = get_recent_chat_messages()[-1]
        assert loaded.actions == actions

    def test_invalid_role_raises(self, temp_db):
        with pytest.raises(ValueError):
            save_chat_message("system", "nope")

    def test_recent_messages_chronological(self, temp_db):
        save_chat_message("user", "first")
        save_chat_message("assistant", "second")
        save_chat_message("user", "third")
        contents = [m.content for m in get_recent_chat_messages()]
        assert contents == ["first", "second", "third"]

    def test_limit_returns_most_recent_chronological(self, temp_db):
        for i in range(5):
            save_chat_message("user", f"msg{i}")
        recent = get_recent_chat_messages(limit=2)
        assert [m.content for m in recent] == ["msg3", "msg4"]

    def test_default_limit_is_twenty(self, temp_db):
        for i in range(25):
            save_chat_message("user", f"msg{i}")
        assert len(get_recent_chat_messages()) == 20

    def test_isolation_between_users(self, temp_db):
        save_chat_message("user", "hi", user_id="alice")
        assert len(get_recent_chat_messages(user_id="alice")) == 1
        assert len(get_recent_chat_messages(user_id="default")) == 0
