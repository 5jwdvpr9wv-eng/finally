"""Tests for users_profile repository functions."""

from app.db import get_user_profile, set_cash_balance
from app.db.models import UserProfile


class TestUserProfile:
    def test_get_seeded_profile(self, temp_db):
        profile = get_user_profile()
        assert isinstance(profile, UserProfile)
        assert profile.id == "default"
        assert profile.cash_balance == 10000.0

    def test_get_creates_profile_for_new_user(self, temp_db):
        profile = get_user_profile("alice")
        assert profile.id == "alice"
        assert profile.cash_balance == 10000.0
        assert profile.created_at

    def test_set_cash_balance(self, temp_db):
        updated = set_cash_balance(8500.25)
        assert updated.cash_balance == 8500.25
        # Round-trips through a fresh read.
        assert get_user_profile().cash_balance == 8500.25

    def test_set_cash_balance_for_missing_user_creates_then_sets(self, temp_db):
        updated = set_cash_balance(500.0, user_id="bob")
        assert updated.id == "bob"
        assert updated.cash_balance == 500.0
