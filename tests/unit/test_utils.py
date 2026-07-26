import pytest

from rfvibium.errors import VibiumLibraryError
from rfvibium.utils import parse_timeout_ms


def test_parse_timeout_ms_with_seconds() -> None:
    assert parse_timeout_ms("1.5s") == 1500


def test_parse_timeout_ms_with_milliseconds_suffix() -> None:
    assert parse_timeout_ms("250ms") == 250


def test_parse_timeout_ms_with_plain_number() -> None:
    assert parse_timeout_ms("300") == 300


def test_parse_timeout_ms_with_minutes() -> None:
    assert parse_timeout_ms("1m") == 60_000
    assert parse_timeout_ms("1 min") == 60_000
    assert parse_timeout_ms("1.5min") == 90_000


def test_parse_timeout_ms_allows_zero() -> None:
    assert parse_timeout_ms("0") == 0
    assert parse_timeout_ms("0s") == 0


def test_parse_timeout_ms_rejects_empty() -> None:
    with pytest.raises(VibiumLibraryError, match="empty"):
        parse_timeout_ms("   ")


def test_parse_timeout_ms_rejects_invalid() -> None:
    with pytest.raises(VibiumLibraryError, match="Invalid timeout"):
        parse_timeout_ms("abc")


def test_parse_timeout_ms_rejects_negative() -> None:
    with pytest.raises(VibiumLibraryError, match="negative"):
        parse_timeout_ms("-1s")
    with pytest.raises(VibiumLibraryError, match="negative"):
        parse_timeout_ms("-100")
