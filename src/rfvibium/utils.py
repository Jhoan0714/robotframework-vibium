"""Internal helpers shared by keyword modules."""

from __future__ import annotations

from .errors import VibiumLibraryError


def parse_timeout_ms(timeout: str) -> int:
    """Parse Robot-style timeout to milliseconds.

    Supported formats:
    - ``500`` (milliseconds)
    - ``500ms``
    - ``2s`` / ``1.5s``
    - ``1m`` / ``1 min`` / ``1min`` (minutes)

    Raises:
        VibiumLibraryError: If the value is empty, not a number, or negative.
    """
    raw = timeout.strip().lower()
    if not raw:
        raise VibiumLibraryError("Timeout cannot be empty.")

    # Allow "1 min" / "1.5 s" style spacing.
    value = "".join(raw.split())

    try:
        if value.endswith("ms"):
            ms = int(float(value[:-2]))
        elif value.endswith("min"):
            ms = int(float(value[:-3]) * 60_000)
        elif value.endswith("m"):
            ms = int(float(value[:-1]) * 60_000)
        elif value.endswith("s"):
            ms = int(float(value[:-1]) * 1000)
        else:
            ms = int(float(value))
    except ValueError as exc:
        raise VibiumLibraryError(
            f"Invalid timeout {timeout!r}. Use ms, s, m/min, or a plain number."
        ) from exc

    if ms < 0:
        raise VibiumLibraryError(f"Timeout cannot be negative (got {timeout!r}).")
    return ms
