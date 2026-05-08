from rfvibium.utils import parse_timeout_ms


def test_parse_timeout_ms_with_seconds() -> None:
    assert parse_timeout_ms("1.5s") == 1500


def test_parse_timeout_ms_with_milliseconds_suffix() -> None:
    assert parse_timeout_ms("250ms") == 250


def test_parse_timeout_ms_with_plain_number() -> None:
    assert parse_timeout_ms("300") == 300
