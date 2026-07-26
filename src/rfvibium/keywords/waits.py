"""Synchronization keywords.

Vibium exposes **two different “wait” surfaces**; the Robot keywords here map
to one or the other:

**1) Page-level waits** (``async_api/page.py`` — property ``Page.wait_until``)

This is a *namespace* object. It is **not** the same as ``Element.wait_until``.

- Calling it like a function — ``page.wait_until(fn, timeout=...)`` — runs
  ``Page._wait_for_function`` (protocol ``vibium:page.waitForFunction``): wait
  until a **JavaScript snippet** evaluates to something truthy.
- ``page.wait_until.url(pattern, ...)`` → ``vibium:page.waitForURL``.
- ``page.wait_until.loaded(state=..., ...)`` → ``vibium:page.waitForLoad``.
  Which ``state`` strings are accepted and how they map is defined by **Vibium**.
- ``page.wait(ms)`` → ``vibium:page.wait`` (fixed delay; unrelated to
  ``wait_until``).

**Keywords using the Page API:** ``Wait For Text``, ``Wait For Function``,
``Wait For Url``, ``Wait For Load State``, ``Page Wait`` (alias:
``Sleep Milliseconds``).

**2) Element-level wait** (``async_api/element.py`` — method ``Element.wait_until``)

After ``page.find(...)`` you get an ``Element``. Its method
``element.wait_until(state=..., timeout=...)`` maps to ``vibium:element.waitFor``
and waits for DOM **lifecycle / visibility** states: ``visible``, ``hidden``,
``attached``, ``detached``.

**Keyword using the Element API:** ``Wait For Element``.
"""

from __future__ import annotations

from robot.api import logger
from robot.api.deco import keyword

from ..errors import LocatorSyntaxError, VibiumLibraryError
from ..locator import format_locators, resolve_required_locators
from ..utils import parse_timeout_ms

_ELEMENT_WAIT_STATES: frozenset[str] = frozenset(
    {"visible", "hidden", "attached", "detached"}
)

_SLEEP_MS_MAX = 30_000


class WaitKeywords:
    """Explicit waits; see module docstring for Page vs Element mapping."""

    def __init__(self, library):
        self.library = library

    @keyword("Wait For Text")
    def wait_for_text(self, text: str, timeout: str = "10s") -> None:
        """Wait until text appears in the visible page body.

        | =Argument= | =Description= |
        | ``text`` | Text fragment to wait for in ``document.body.innerText``. |
        | ``timeout`` | Robot Framework timeout string. Default is ``10s``. |

        Note:
            Uses page-level ``wait_until(...)`` behavior (waitForFunction).

        Example:
            | Wait For Text    Welcome back    timeout=5s
        """
        page = self.library._session.require_page()
        timeout_ms = parse_timeout_ms(timeout)
        logger.info(f"Waiting for text '{text}' on page (timeout={timeout}).")
        page.wait_until(
            f"() => document.body && document.body.innerText.includes({text!r})",
            timeout=timeout_ms,
        )

    @keyword("Wait For Load State")
    def wait_for_load_state(self, state: str = "loading", timeout: str = "10s") -> None:
        """Wait until the page reaches a load state (delegates to Vibium).

        The ``state`` argument is passed through to ``page.wait_until.loaded``
        without rewriting; refer to Vibium's ``waitForLoad`` / page API for valid
        values and semantics.

        | =Argument= | =Description= |
        | ``state`` | Load-state token understood by Vibium. Default is ``loading``. |
        | ``timeout`` | Robot Framework timeout string. Default is ``10s``. |

        Example:
            | Wait For Load State    complete    timeout=15s
        """
        page = self.library._session.require_page()
        timeout_ms = parse_timeout_ms(timeout)
        logger.info(f"Waiting for load state '{state}' (timeout={timeout}).")
        page.wait_until.loaded(state=state, timeout=timeout_ms)

    @keyword("Wait For Element")
    def wait_for_element(
        self,
        *locators: str,
        state: str = "visible",
        timeout: str = "10s",
    ) -> None:
        """Wait until a matched element reaches a target state.

        | =Argument= | =Description= |
        | ``*locators`` | Locator tokens used to resolve a single element via ``page.find(...)``. |
        | ``state`` | Target element state: ``visible``, ``hidden``, ``attached``, or ``detached``. Default is ``visible``. |
        | ``timeout`` | Robot Framework timeout string. Default is ``10s``. |

        Raises:
            LocatorSyntaxError: If ``state`` is not supported.

        Example:
            | Wait For Element    css:#modal    state=visible    timeout=5s
            | Wait For Element    role:dialog    text:Saving    state=hidden
        """
        page = self.library._session.require_page()
        normalized = state.strip().lower()
        if normalized not in _ELEMENT_WAIT_STATES:
            raise LocatorSyntaxError(
                f"Wait For Element: state must be one of "
                f"{', '.join(sorted(_ELEMENT_WAIT_STATES))}; got {state!r}."
            )
        timeout_ms = parse_timeout_ms(timeout)
        args, kwargs = resolve_required_locators(locators)
        logger.info(
            f"Waiting for element '{format_locators(locators)}' "
            f"to become '{normalized}' (timeout={timeout})."
        )
        page.find(*args, **kwargs).wait_until(state=normalized, timeout=timeout_ms)

    @keyword("Wait For Url")
    def wait_for_url(self, pattern: str, timeout: str = "10s") -> None:
        """Wait until page URL matches the provided pattern fragment.

        | =Argument= | =Description= |
        | ``pattern`` | URL fragment/pattern accepted by Vibium ``wait_until.url(...)``. |
        | ``timeout`` | Robot Framework timeout string. Default is ``10s``. |

        Example:
            | Wait For Url    /dashboard    timeout=15s
        """
        page = self.library._session.require_page()
        timeout_ms = parse_timeout_ms(timeout)
        logger.info(f"Waiting for URL to contain '{pattern}' (timeout={timeout}).")
        page.wait_until.url(pattern, timeout=timeout_ms)

    @keyword("Wait For Function")
    def wait_for_function(self, expression: str, timeout: str = "10s") -> None:
        """Wait until a JavaScript expression evaluates to truthy.

        | =Argument= | =Description= |
        | ``expression`` | JavaScript function/expression string evaluated in the page context. |
        | ``timeout`` | Robot Framework timeout string. Default is ``10s``. |

        Raises:
            LocatorSyntaxError: If ``expression`` is empty.

        Example:
            | Wait For Function    () => document.querySelector('.done') !== null
        """
        page = self.library._session.require_page()
        stripped = expression.strip()
        if not stripped:
            raise LocatorSyntaxError("Wait For Function: expression cannot be empty.")
        timeout_ms = parse_timeout_ms(timeout)
        logger.info(f"Waiting for JS condition (timeout={timeout}).")
        page.wait_until(stripped, timeout=timeout_ms)

    @keyword("Page Wait")
    def page_wait(self, milliseconds: object) -> None:
        """Sleep for a fixed number of milliseconds on the active page.

        | =Argument= | =Description= |
        | ``milliseconds`` | Number or numeric string in milliseconds. Must be between ``0`` and ``30000``. |

        Raises:
            VibiumLibraryError: If value is invalid, negative, or above 30000.

        Example:
            | Page Wait    500
        """
        page = self.library._session.require_page()
        ms = WaitKeywords._coerce_sleep_ms(milliseconds)
        if ms < 0:
            raise VibiumLibraryError(f"Page Wait: value cannot be negative (got {ms}).")
        if ms > _SLEEP_MS_MAX:
            raise VibiumLibraryError(
                f"Page Wait: value {ms} exceeds maximum {_SLEEP_MS_MAX} ms."
            )
        logger.info(f"Page wait {ms} ms.")
        page.wait(ms)

    @keyword("Sleep Milliseconds")
    def sleep_milliseconds(self, milliseconds: object) -> None:
        """Alias of ``Page Wait``.

        | =Argument= | =Description= |
        | ``milliseconds`` | Number or numeric string in milliseconds. Same behavior as ``Page Wait``. |
        """
        self.page_wait(milliseconds)

    @staticmethod
    def _coerce_sleep_ms(milliseconds: object) -> int:
        if isinstance(milliseconds, bool):
            raise VibiumLibraryError(
                f"Page Wait: expected a number, not boolean ({milliseconds!r})."
            )
        if isinstance(milliseconds, int):
            return milliseconds
        if isinstance(milliseconds, float):
            return int(milliseconds)
        if isinstance(milliseconds, str):
            raw = milliseconds.strip()
            if not raw:
                raise VibiumLibraryError("Page Wait: value cannot be empty.")
            try:
                return int(float(raw))
            except ValueError as exc:
                raise VibiumLibraryError(
                    f"Page Wait: value must be a number, got {milliseconds!r}."
                ) from exc
        raise VibiumLibraryError(
            "Page Wait: value must be a number or numeric string, "
            f"got {type(milliseconds).__name__}."
        )
