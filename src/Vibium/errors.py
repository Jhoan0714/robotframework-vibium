"""Domain-specific exceptions for the Vibium Robot Framework library.

All library errors inherit from :class:`VibiumLibraryError` so users can
catch either a specific subclass or the base class for a broader net::

    TRY
        Click Element    role:button
    EXCEPT    AS    ${err}
        Log    ${err}
    END

The subclasses let tests / user code discriminate by failure kind:

- :class:`LocatorSyntaxError` — the locator / arguments handed to a
  keyword are malformed. Fail fast, do not retry.
- :class:`BrowserSessionError` — the browser session is missing or the
  underlying browser process failed to start / stop.
- :class:`ScreenshotError` — a screenshot capture failed after retries.

Element-not-found conditions are intentionally *not* re-typed: vibium
already raises a clearly named ``ElementNotFoundError`` that Robot
Framework's ``EXCEPT ElementNotFoundError`` matches by class name.
"""


class VibiumLibraryError(RuntimeError):
    """Base class for all errors raised by ``robotframework-vibium``."""


class LocatorSyntaxError(VibiumLibraryError):
    """Raised when a locator string or keyword argument is malformed."""


class BrowserSessionError(VibiumLibraryError):
    """Raised for browser session lifecycle failures.

    Examples: no active page when a keyword that needs one runs, the
    browser process failed to start or stop, or the BiDi connection was
    lost and cannot be recovered.
    """


class ScreenshotError(VibiumLibraryError):
    """Raised when a screenshot cannot be captured or written to disk."""
