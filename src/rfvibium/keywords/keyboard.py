"""Page-level keyboard keywords mapped to Vibium ``Page.keyboard`` (sync API)."""

from __future__ import annotations

from robot.api import logger
from robot.api.deco import keyword

from ..errors import VibiumLibraryError

_KEY_ACTIONS = {
    "down": "down",
    "up": "up",
    "press": "press",
}


class KeyboardKeywords:
    """Low-level keyboard input on the active page."""

    def __init__(self, library):
        self.library = library

    @staticmethod
    def _normalize_action(action: object) -> str:
        raw = action.strip().lower() if isinstance(action, str) else ""
        normalized = _KEY_ACTIONS.get(raw)
        if normalized is None:
            allowed = ", ".join(sorted(_KEY_ACTIONS))
            raise VibiumLibraryError(
                f"action must be one of: {allowed}. Got {action!r}."
            )
        return normalized

    @keyword("Keyboard Type")
    def keyboard_type(self, text: str, scope: object = None) -> None:
        """Type ``text`` character by character via the page keyboard.

        Unlike ``Fill Text``, this sends key events and does not target a
        specific element locator. For a single key or combo, use
        ``Keyboard Key``.

        | =Argument= | =Description= |
        | ``text`` | Text to type. |
        | ``scope`` | Optional page/frame object. When omitted, uses the active scope. |

        Example:
            | Keyboard Type    hello world
        """
        page = self.library._session.resolve_scope(scope)
        display = text if len(text) <= 40 else f"{text[:37]}..."
        logger.info(f"Keyboard type {display!r}.")
        page.keyboard.type(text)

    @keyword("Keyboard Key")
    def keyboard_key(self, action: str, key: str, scope: object = None) -> None:
        """Send a page-level key action (``down``, ``up``, or ``press``).

        ``press`` sends a full keystroke (or combo such as ``Control+a``).
        ``down`` / ``up`` hold or release a key without the matching event.

        | =Argument= | =Description= |
        | ``action`` | ``down``, ``up``, or ``press`` (case-insensitive). |
        | ``key`` | Keyboard key or combo supported by Vibium (for example ``Shift``, ``Enter``, ``Control+a``). |
        | ``scope`` | Optional page/frame object. When omitted, uses the active scope. |

        Example:
            | Keyboard Key    press    Enter
            | Keyboard Key    press    Control+a
            | Keyboard Key    down    Shift
            | Keyboard Key    press    ArrowDown
            | Keyboard Key    up    Shift
        """
        page = self.library._session.resolve_scope(scope)
        action_name = KeyboardKeywords._normalize_action(action)
        logger.info(f"Keyboard {action_name} '{key}'.")
        getattr(page.keyboard, action_name)(key)
