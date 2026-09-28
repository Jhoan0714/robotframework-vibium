"""Robot Framework argument converters (Libdoc Data Types + runtime).

Registered on the library via ``@library(converters=...)``. Parameter
annotations must not use ``Any``: Robot Framework uses them as
``value_types`` and ``isinstance(..., Any)`` raises TypeError.
"""

from __future__ import annotations

from typing import Union

from assertionengine import AssertionOperator
from vibium import Element
from vibium.sync_api import Browser, BrowserContext, Page

from .assertions.helper import parse_assertion_operator


def convert_assertion_operator(
    value: Union[str, AssertionOperator],
) -> AssertionOperator:
    """AssertionEngine comparison operator (e.g. ``==``, ``contains``, ``*=``).

    Used by getter keywords with optional ``assertion_operator=`` /
    ``assertion_expected=``. Accepts enum members or Robot-friendly string
    aliases.
    """
    if isinstance(value, AssertionOperator):
        return value
    op = parse_assertion_operator(value)
    if op is None:
        raise ValueError(
            f"Invalid assertion operator: {value!r}. "
            "Use AssertionEngine operators such as ==, !=, contains, *=."
        )
    return op


def convert_browser(value: Browser) -> Browser:
    """Browser session handle from ``Open Browser``.

    Pass as ``browser=`` to keywords that target a specific browser instance
    (for example ``New Page``, ``List Pages``, ``Close Browser``).
    """
    if isinstance(value, Browser):
        return value
    raise TypeError(f"Expected Browser, got {type(value).__name__}.")


def convert_browser_context(value: BrowserContext) -> BrowserContext:
    """Browser context handle (isolated profile: cookies, storage).

    Created by ``New Context`` or returned by ``Get Active Context``. Pass as
    ``context=`` to cookie/storage and page keywords.
    """
    if isinstance(value, BrowserContext):
        return value
    raise TypeError(f"Expected BrowserContext, got {type(value).__name__}.")


def convert_page(value: Page) -> Page:
    """Page or frame handle from Vibium.

    Pass as ``scope=`` / ``page=`` to keywords that target a browsing context.
    Frames returned by ``Get Frame`` are also ``Page`` objects.
    """
    if isinstance(value, Page):
        return value
    raise TypeError(f"Expected Page, got {type(value).__name__}.")


def convert_element(value: Element) -> Element:
    """Element handle from ``Find Element`` / ``Find Elements``.

    Pass as ``scope=`` for nested finds, or as the sole ``*locators`` target
    on action/getter keywords. Use ``Describe Element`` for a readable string.
    """
    if isinstance(value, Element):
        return value
    raise TypeError(f"Expected Element, got {type(value).__name__}.")
