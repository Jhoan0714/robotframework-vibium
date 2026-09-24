"""Library configuration keywords (timeouts, scopes)."""

from __future__ import annotations

from robot.api import logger
from robot.api.deco import keyword

from ..config.settings import parse_scope
from ..utils import parse_timeout_ms, timeout_ms_to_timestr


class ConfigKeywords:
    """Keywords that configure library-wide defaults."""

    def __init__(self, library):
        self.library = library

    @keyword("Set Browser Timeout", tags=["Config", "Action"])
    def set_browser_timeout(self, timeout: str, scope: str = "Suite") -> str:
        """Set the default timeout for element locate/actions.

        Used when a keyword omits ``timeout=``. Per-call ``timeout=`` still wins.

        | =Argument= | =Description= |
        | ``timeout`` | Robot time string (e.g. ``5s``, ``500ms``). Use ``None`` or empty to clear the override (Vibium default). |
        | ``scope`` | ``Global``, ``Suite`` (default), or ``Test`` / ``Task``. See Scope Setting. |

        Returns the previous timeout as a Robot time string, or ``None`` when
        there was no library override (Vibium default).

        Example:
            | ${old}=    Set Browser Timeout    2s
            | Click    css:#save
            | Set Browser Timeout    ${old}
            | Set Browser Timeout    500ms    scope=Test
        """
        old_ms = self.library.timeout_settings.get()
        old_str = timeout_ms_to_timestr(old_ms)
        new_ms = _coerce_set_timeout(timeout)
        resolved_scope = parse_scope(scope)
        self.library.timeout_settings.set(new_ms, resolved_scope)
        logger.info(
            f"Browser timeout set to {timeout_ms_to_timestr(new_ms)!r} "
            f"(scope={resolved_scope.value})."
        )
        return old_str


def _coerce_set_timeout(timeout: object) -> int | None:
    if timeout is None:
        return None
    raw = str(timeout).strip()
    if not raw or raw.lower() == "none":
        return None
    return parse_timeout_ms(raw)
