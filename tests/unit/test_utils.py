import pytest

from rfvibium.errors import VibiumLibraryError
from rfvibium.utils import coerce_viewport_axis, optional_timeout_ms, parse_timeout_ms


def test_coerce_viewport_axis_accepts_number_and_string() -> None:
    assert coerce_viewport_axis("x", 10) == 10.0
    assert coerce_viewport_axis("y", "1.5", kind="Touch") == 1.5


def test_coerce_viewport_axis_rejects_none_and_empty() -> None:
    with pytest.raises(VibiumLibraryError, match="Mouse x must be a number"):
        coerce_viewport_axis("x", None)
    with pytest.raises(VibiumLibraryError, match="Touch y cannot be an empty"):
        coerce_viewport_axis("y", "  ", kind="Touch")


def test_coerce_viewport_axis_rejects_bool() -> None:
    with pytest.raises(VibiumLibraryError, match="not a boolean"):
        coerce_viewport_axis("x", True)


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


def test_optional_timeout_ms_none_or_blank() -> None:
    assert optional_timeout_ms(None) is None
    assert optional_timeout_ms("") is None
    assert optional_timeout_ms("   ") is None


def test_optional_timeout_ms_parses_value() -> None:
    assert optional_timeout_ms("500ms") == 500
    assert optional_timeout_ms("2s") == 2000
