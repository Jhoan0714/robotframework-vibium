"""Internal helpers shared by keyword modules."""

from __future__ import annotations


def parse_timeout_ms(timeout: str) -> int:
    """Parse Robot-style timeout to milliseconds.

    Supported formats:
    - ``500`` (milliseconds)
    - ``500ms``
    - ``2s``
    - ``1.5s``
    """
    value = timeout.strip().lower()
    if value.endswith("ms"):
        return int(float(value[:-2]))
    if value.endswith("s"):
        return int(float(value[:-1]) * 1000)
    return int(float(value))
