"""Internal helpers shared by keyword modules."""

from __future__ import annotations

from robot.utils import timestr_to_secs

from .errors import VibiumLibraryError


def coerce_viewport_axis(name: str, value: object, *, kind: str = "Mouse") -> float:
    """Coerce a viewport axis (or delta) to ``float`` for mouse/touch keywords.

    Args:
        name: Axis label used in errors (``x``, ``y``, ``delta_x``, …).
        value: Number or numeric string from Robot Framework.
        kind: Device label prefixed in errors (``Mouse``, ``Touch``, …).

    Raises:
        VibiumLibraryError: If ``value`` is missing, empty, boolean, or non-numeric.
    """
    if value is None:
        raise VibiumLibraryError(
            f"{kind} {name} must be a number (viewport pixels); got none/omitted."
        )
    if isinstance(value, bool):
        raise VibiumLibraryError(
            f"{kind} {name} must be a number, not a boolean ({value!r})."
        )
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        raw = value.strip()
        if not raw:
            raise VibiumLibraryError(f"{kind} {name} cannot be an empty string.")
        try:
            return float(raw)
        except ValueError as exc:
            raise VibiumLibraryError(
                f"{kind} {name} must be a number, got {value!r}."
            ) from exc
    raise VibiumLibraryError(
        f"{kind} {name} must be a number, got {type(value).__name__}: {value!r}."
    )


def parse_timeout_ms(timeout: str) -> int:
    """Parse a Robot Framework time string to milliseconds for Vibium.

    Uses ``robot.utils.timestr_to_secs``.
    A bare number is **seconds** (e.g. ``300`` → 300_000 ms). Prefer an
    explicit unit (``5s``, ``500ms``, ``1 min``).

    Raises:
        VibiumLibraryError: If the value is empty, invalid, or negative.
    """
    raw = timeout.strip()
    if not raw:
        raise VibiumLibraryError("Timeout cannot be empty.")
    try:
        secs = timestr_to_secs(raw)
    except ValueError as exc:
        raise VibiumLibraryError(
            f"Invalid timeout {timeout!r}. Use Robot time format "
            f"(e.g. '5s', '500ms', '1 min'); a bare number is seconds."
        ) from exc
    ms = int(secs * 1000)
    if ms < 0:
        raise VibiumLibraryError(f"Timeout cannot be negative (got {timeout!r}).")
    return ms


def optional_timeout_ms(timeout: object | None) -> int | None:
    """Parse an optional Robot timeout string to milliseconds.

    Returns ``None`` when ``timeout`` is omitted or blank so callers can pass
    Vibium's default. Non-empty values use :func:`parse_timeout_ms`.
    """
    if timeout is None:
        return None
    raw = str(timeout).strip()
    if not raw:
        return None
    return parse_timeout_ms(raw)
