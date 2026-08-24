"""Public Robot Framework library class."""

from __future__ import annotations

from robot.api import logger
from robot.api.deco import keyword, library
from robotlibcore import DynamicCore

from .browser_session import SessionPool
from .keywords.assertions import AssertionKeywords
from .keywords.capture import CaptureKeywords
from .keywords.context import CookieKeywords, StorageKeywords
from .keywords.dialogs import DialogKeywords
from .keywords.interaction import InteractionKeywords
from .keywords.mouse import MouseKeywords
from .keywords.navigation import NavigationKeywords
from .keywords.waits import WaitKeywords
from .version import __version__


@library(scope="GLOBAL", version=__version__, doc_format="ROBOT")
class Vibium(DynamicCore):
    """Vibium library is a browser automation library for Robot Framework.

    This is the keyword documentation for Vibium. The library exposes browser
    automation through Robot keywords focused on readability, robust locators,
    and practical defaults for UI testing.

    Repository and docs:
    - Project: [https://github.com/Jhoan0714/robotframework-vibium|robotframework-vibium]
    - Vibium: [https://github.com/VibiumDev/vibium|VibiumDev/vibium]
    - Robot Framework: [https://robotframework.org|robotframework.org]

    *Table of contents*

    %TOC%

    = Importing =

    Import the library in Robot Framework:

    | *** Settings ***
    | Library    Vibium

    The default scope is ``GLOBAL`` (one library instance for the full run).

    = Browser Lifecycle =

    == Browser ==

    ``Open Browser`` starts a browser instance and returns its handle.
    When multiple browsers are open, some navigation/context keywords accept
    ``browser=`` so you can target a specific browser handle.

    == Context ==

    A context is an isolated browser profile inside a browser (cookies/storage scope).
    New pages are opened inside a context, and context keywords let you inspect,
    switch, and close that isolation boundary.

    == Page ==

    The library tracks an *active* page used by defaulted keywords.
    Keywords that accept ``scope`` use that active page when ``scope`` is omitted,
    or use the explicit page/frame you pass. Passing ``scope`` does not change
    the global active page unless a keyword explicitly updates it (for example
    ``Switch Page``).

    = Locating Elements =

    Most interaction/getter keywords accept one or more locator tokens.
    Tokens are merged into a single ``page.find(...)`` call, so you can combine
    multiple constraints (for example role + text) to target one element with
    better precision.

    = Supported locator strategies =

    | =Strategy= | =Description= | =Example= |
    | ``css`` | CSS selector (default when no prefix is provided). | ``css:button.primary`` |
    | ``role`` | Accessible role. | ``role:button`` |
    | ``text`` | Visible text content. | ``text:Save`` |
    | ``label`` | Accessible label (form-oriented). | ``label:Email`` |
    | ``placeholder`` | Input placeholder text. | ``placeholder:Type your email`` |
    | ``testid`` | Test id attribute. | ``testid:login-submit`` |
    | ``alt`` | Alt text (images/media). | ``alt:Company logo`` |
    | ``title`` | Title attribute/text. | ``title:Open settings`` |
    | ``xpath`` | XPath expression. | ``xpath://button[@type='submit']`` |
    | ``near`` | Element near another text/selector hint. | ``near:Password`` |

    = Explicit strategy syntax =

    Use ``strategy:value`` to force a specific strategy:

    | Click    text:Sign in
    | Fill Text     label:Email    user@example.com
    | Click    xpath://button[@id='submit']

    = Implicit strategy (default) =

    If a token does not include a known ``strategy:`` prefix, it is treated as
    a CSS selector.

    | Click    button.primary
    | Find Element     #login-form input[name='email']

    = Combining locator tokens =

    Passing multiple tokens narrows the match. This is useful when one strategy
    alone is ambiguous.

    | Click    role:button    text:Continue
    | Fill Text     role:textbox   label:Email    value=user@example.com

    = Practical guidance =

    Prefer semantic strategies (``role``, ``label``, ``text``, ``testid``)
    before deep CSS/XPath selectors when possible. Semantic locators are usually
    more stable and easier to understand in test logs.

    = Interaction and Getters =

    Element actions (click, fill, type, select, drag, upload, key press) and
    getter keywords (text, html, value, attributes, bounds, state) are provided
    by the interaction keyword set.

    = Assertions =

    Read/assertion-oriented keywords provide page and element state retrieval,
    such as URL, title, page HTML, element counting, and JavaScript evaluation.

    = Timeouts, Waits and Delays =

    Wait keywords provide explicit synchronization:
    - wait for text
    - wait for load state
    - wait for element state
    - page sleep/wait utilities

    = Artifacts: Screenshots, PDF, Storage =

    Vibium can capture runtime artifacts:
    - page screenshot
    - element screenshot
    - page PDF
    - storage state export/restore

    Relative artifact paths are resolved under Robot ``${OUTPUT DIR}/media/``
    when running inside Robot Framework.

    = Cookies and Storage =

    Cookie and storage keywords allow tests to inspect, set, clear, export, and
    restore browser state for setup/teardown and stateful flows.

    = Scope Setting =

    ``ROBOT_LIBRARY_SCOPE`` is ``GLOBAL``. The same Vibium instance is reused
    across suites and tests in a single execution.

    = Typical usage =

    | *** Test Cases ***
    | Basic Flow
    |     Open Browser
    |     Go To    https://example.com
    |     Fill Text    role:textbox    user@example.com
    |     Click   role:button    text:Submit
    |     Close Browser

    """

    ROBOT_LIBRARY_SCOPE = "GLOBAL"
    ROBOT_LIBRARY_VERSION = __version__

    def __init__(self, headless: bool = False):
        self._session = SessionPool(headless=headless)
        components = [
            NavigationKeywords(self),
            MouseKeywords(self),
            InteractionKeywords(self),
            AssertionKeywords(self),
            CaptureKeywords(self),
            CookieKeywords(self),
            StorageKeywords(self),
            DialogKeywords(self),
            WaitKeywords(self),
        ]
        DynamicCore.__init__(self, components)

    @keyword("Open Browser")
    def open_browser(self, engine: str | None = None, channel: str | None = None):
        """Open a new Browser session and return its handle.

        When ``engine`` is omitted, Vibium uses Chrome by default or the engine
        set via the ``VIBIUM_ENGINE`` environment variable.

        | =Argument= | =Description= |
        | ``engine`` | Optional browser engine: ``chrome`` (default) or ``firefox``. |
        | ``channel`` | Optional Firefox release channel: ``release`` (default) or ``beta``. Firefox only. |

        | *** Test Cases ***
        | Chrome Default
        |     Open Browser
        |     Go To    https://example.com
        | Firefox
        |     Open Browser    engine=firefox
        |     Go To    https://example.com
        """
        engine = engine.lower() if engine else engine
        channel = channel.lower() if channel else channel
        browser = self._session.open(engine=engine, channel=channel)
        logger.info("Browser session opened.")
        return browser

    @keyword("Close Browser")
    def close_browser(self, browser=None) -> None:
        """Close one Browser session (active browser by default)."""
        self._session.close(browser=browser)
        logger.info("Browser session closed.")

    @keyword("Close All Browsers")
    def close_all_browsers(self) -> None:
        """Close all Browser sessions created by this library instance."""
        self._session.close_all()
        logger.info("All Browser sessions closed.")
