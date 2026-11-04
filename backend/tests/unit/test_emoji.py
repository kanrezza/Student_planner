"""Kiểm tra "đúng một emoji" không cần thư viện (feature 002 FR-015, task T025)."""

import pytest

from app.schemas.tasks import is_single_emoji


@pytest.mark.parametrize("text", ["🏠", "❤️", "👍🏽", "👨‍👩‍👧", "🇻🇳", "☕", "✅", "📚"])
def test_single_emoji(text):
    assert is_single_emoji(text)


@pytest.mark.parametrize(
    "text", ["a", "ab", "🏠🏠", "🏠a", " 🏠", "🏠 ", "1️⃣", "", "🇻", "🇻🇳🇻", "‍🏠", "🏠‍"]
)
def test_not_single_emoji(text):
    assert not is_single_emoji(text)
