"""Internal helpers shared by keyword modules."""

from __future__ import annotations

from typing import Any

from robot.utils import secs_to_timestr, timestr_to_secs

from .errors import VibiumLibraryError


def coerce_int(value: Any) -> Any:
    """Coerce Robot-friendly scalars to ``int`` when unambiguous.

    Accepts ``int``, integer-valued ``float``, and numeric strings (``\"2\"``,
    ``\"2.0\"``). ``None`` and non-integer values that cannot be coerced are
    returned unchanged or raise ``ValueError`` for bad strings.

    Useful when AssertionEngine compares ints and Robot passes string numbers
    (e.g. ``Count Elements … == ${2}`` on AssertionEngine 3.0.x / Python 3.9).
    """
    if value is None or isinstance(value, bool):
        return value
    if isinstance(value, int):
        return value
    if isinstance(value, float) and value.is_integer():
        return int(value)
    if isinstance(value, str):
        stripped = value.strip()
        try:
            return int(stripped)
        except ValueError:
            try:
                as_float = float(stripped)
            except ValueError as exc:
                raise ValueError(f"Expected an integer, got {value!r}.") from exc
            if as_float.is_integer():
                return int(as_float)
            raise ValueError(f"Expected an integer, got {value!r}.") from None
    return value


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


def optional_timeout_ms(
    timeout: object | None, *, library: object | None = None
) -> int | None:
    """Resolve an optional keyword timeout to milliseconds.

    Precedence:

    1. Explicit non-blank ``timeout`` argument → :func:`parse_timeout_ms`
    2. Library ``Set Browser Timeout`` stack (when ``library`` is passed)
    3. ``None`` → Vibium built-in default
    """
    if timeout is not None:
        raw = str(timeout).strip()
        if raw:
            return parse_timeout_ms(raw)
    if library is not None:
        stack = getattr(library, "timeout_stack", None)
        if stack is not None:
            return stack.get()
    return None


def timeout_ms_to_timestr(ms: int | None) -> str:
    """Format milliseconds as a Robot time string, or ``None`` when unset."""
    if ms is None:
        return "None"
    return secs_to_timestr(ms / 1000.0)
