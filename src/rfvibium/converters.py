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

# AssertionEngine ships Robot-format tables in ``AssertionOperator.__doc__``.
# Libdoc uses that Enum docstring for Data Types; with library ``doc_format``
# Markdown those tables render as raw pipes. Replace with Markdown equivalent
# (same content) so Documentation stays readable. Allowed Values unchanged.
AssertionOperator.__doc__ = """\
Currently supported assertion operators are:

| Operator | Alternative Operators | Description | Validate Equivalent |
| -------- | --------------------- | ----------- | ------------------- |
| ``==`` | ``equal``, ``equals``, ``should be`` | Checks if returned value is equal to expected value. | ``value == expected`` |
| ``!=`` | ``inequal``, ``should not be`` | Checks if returned value is not equal to expected value. | ``value != expected`` |
| ``>`` | ``greater than`` | Checks if returned value is greater than expected value. | ``value > expected`` |
| ``>=`` | | Checks if returned value is greater than or equal to expected value. | ``value >= expected`` |
| ``<`` | ``less than`` | Checks if returned value is less than expected value. | ``value < expected`` |
| ``<=`` | | Checks if returned value is less than or equal to expected value. | ``value <= expected`` |
| ``*=`` | ``contains`` | Checks if returned value contains expected value as substring. | ``expected in value`` |
| | ``not contains`` | Checks if returned value does not contain expected value as substring. | ``expected not in value`` |
| ``^=`` | ``should start with``, ``starts`` | Checks if returned value starts with expected value. | ``re.search(f"^{expected}", value)`` |
| ``$=`` | ``should end with``, ``ends`` | Checks if returned value ends with expected value. | ``re.search(f"{expected}$", value)`` |
| ``matches`` | | Checks if given RegEx matches minimum once in returned value. | ``re.search(expected, value)`` |
| ``validate`` | | Checks if given Python expression evaluates to ``True``. | |
| ``evaluate`` | ``then`` | When using this operator, the keyword does return the evaluated Python expression. | |

Currently supported formatters for assertions are:

| Formatter | Description |
| --------- | ----------- |
| ``normalize spaces`` | Substitutes multiple spaces to single space from the value |
| ``strip`` | Removes spaces from the beginning and end of the value |
| ``case insensitive`` | Converts value to lower case before comparing |
| ``apply to expected`` | Applies rules also for the expected value |

Formatters are applied to the value before assertion is performed and keywords
returns a value where rule is applied. Formatter is only applied to the value
which keyword returns and not all rules are valid for all assertion operators.
If ``apply to expected`` formatter is defined, then formatters are also applied
to expected value.

Upstream: [AssertionEngine](https://github.com/MarketSquare/AssertionEngine).
"""


def convert_assertion_operator(
    value: Union[str, AssertionOperator],
) -> AssertionOperator:
    """Runtime converter for ``AssertionOperator`` (Libdoc docs are on the Enum)."""
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
