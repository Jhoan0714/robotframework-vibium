"""Read-only content and state keywords."""

from __future__ import annotations

from typing import Any

from assertionengine import AssertionOperator
from robot.api import logger
from robot.api.deco import keyword

from ..assertions.helper import (
    assert_value,
    split_locators_and_assertion,
)
from ..errors import LocatorSyntaxError
from ..locators.locator import (
    format_locators,
    resolve_element,
    resolve_required_locators,
)
from ..utils import coerce_int, optional_timeout_ms


class AssertionKeywords:
    """Keywords to read page state."""

    def __init__(self, library):
        self.library = library

    @keyword("Get Url")
    def get_url(
        self,
        assertion_operator: AssertionOperator | None = None,
        assertion_expected: Any = None,
        message: str | None = None,
        *,
        scope: object = None,
    ) -> Any:
        """Return the current URL from the resolved scope.

        Optionally asserts with AssertionEngine.

        | =Argument= | =Description= |
        | ``assertion_operator`` | Optional AssertionEngine operator (e.g. ``==``, ``*=``). |
        | ``assertion_expected`` | Expected value when asserting. |
        | ``message`` | Optional custom assertion failure message. |
        | ``scope`` | Optional page/frame object. When omitted, uses the active scope. |

        Example:
            | ${url}=    Get Url
            | Get Url    *=    /dashboard
            | ${url}=    Get Url    scope=${page}
        """
        page = self.library._session.resolve_scope(scope)
        return assert_value(
            page.url(), assertion_operator, assertion_expected, "URL", message
        )

    @keyword("Get Title")
    def get_title(
        self,
        assertion_operator: AssertionOperator | None = None,
        assertion_expected: Any = None,
        message: str | None = None,
        *,
        scope: object = None,
    ) -> Any:
        """Return the document title from the resolved scope.

        Optionally asserts with AssertionEngine.

        | =Argument= | =Description= |
        | ``assertion_operator`` | Optional AssertionEngine operator. |
        | ``assertion_expected`` | Expected value when asserting. |
        | ``message`` | Optional custom assertion failure message. |
        | ``scope`` | Optional page/frame object. When omitted, uses the active scope. |

        Returns:
            The page title (or AssertionEngine result). The underlying Vibium
            client may return an empty string when no title is available.

        Example:
            | ${title}=    Get Title
            | Get Title    ==    Home
            | ${title}=    Get Title    scope=${page}
        """
        page = self.library._session.resolve_scope(scope)
        return assert_value(
            page.title(), assertion_operator, assertion_expected, "Title", message
        )

    @keyword("Get Page Text")
    def get_page_text(
        self,
        assertion_operator: AssertionOperator | None = None,
        assertion_expected: Any = None,
        message: str | None = None,
        *,
        scope: object = None,
    ) -> Any:
        """Return visible text from ``document.body.innerText`` in the resolved scope.

        Optionally asserts with AssertionEngine.

        | =Argument= | =Description= |
        | ``assertion_operator`` | Optional AssertionEngine operator. |
        | ``assertion_expected`` | Expected value when asserting. |
        | ``message`` | Optional custom assertion failure message. |
        | ``scope`` | Optional page/frame object. When omitted, uses the active scope. |

        Example:
            | ${text}=    Get Page Text
            | Get Page Text    contains    Welcome
            | ${frame_text}=    Get Page Text    scope=${frame}
        """
        page = self.library._session.resolve_scope(scope)
        value = page.evaluate("document.body ? document.body.innerText : ''")
        return assert_value(
            value, assertion_operator, assertion_expected, "Page Text", message
        )

    @keyword("Get Html")
    def get_html(
        self,
        *locators,
        outer: bool = True,
        assertion_operator: AssertionOperator | None = None,
        assertion_expected: Any = None,
        message: str | None = None,
        scope: object = None,
        timeout: str | None = None,
    ) -> Any:
        """Return HTML from the resolved scope or a resolved element.

        Optionally asserts with AssertionEngine. With element locators, trailing
        ``operator`` + ``expected`` may be peeled from ``*locators``; named
        assertion kwargs win over peel.

        | =Argument= | =Description= |
        | ``*locators`` | Optional. Element HTML: locator string(s) or a single element handle. When omitted, reads page-level HTML. Optional trailing assertion operator + expected. |
        | ``outer`` | Controls page-level output when no locators are provided. Default is ``True``. - ``True``: full document HTML via ``page.content()``. - ``False``: body inner HTML via ``document.body.innerHTML``. |
        | ``assertion_operator`` | Optional AssertionEngine operator. |
        | ``assertion_expected`` | Expected value when asserting. |
        | ``message`` | Optional custom assertion failure message. |
        | ``scope`` | Optional page, frame, or parent. Defaults to the active scope. Omit with an element handle. |
        | ``timeout`` | Optional Robot timeout string for locating the element (``find``). Ignored for page-level HTML. |

        Raises:
            LocatorSyntaxError: When locators/handle are provided with ``outer=False``.

        Example:
            | ${doc}=    Get Html
            | ${body}=    Get Html    outer=${FALSE}
            | Get Html    css:.card    contains    <div
            | ${el}=     Find Element    css:.card
            | ${html}=   Get Html    ${el}
        """
        targets, op, expected = split_locators_and_assertion(
            *locators,
            assertion_operator=assertion_operator,
            assertion_expected=assertion_expected,
        )

        if not targets:
            page = self.library._session.resolve_scope(scope)
            if outer:
                value = page.content()
            else:
                value = page.evaluate("document.body ? document.body.innerHTML : ''")
            return assert_value(value, op, expected, "HTML", message)

        if not outer:
            raise LocatorSyntaxError(
                "Get Html with locators supports only outer=True for now."
            )

        timeout_ms = optional_timeout_ms(timeout, library=self.library)
        element = resolve_element(
            self.library._session, *targets, scope=scope, timeout=timeout_ms
        )
        logger.info(f"Reading HTML from element '{format_locators(targets)}'.")
        return assert_value(element.html(), op, expected, "HTML", message)

    @keyword("Find Elements")
    def find_elements(
        self,
        *locators: str,
        limit: int | None = None,
        scope: object = None,
        timeout: str | None = None,
    ) -> list:
        """Return Vibium ``Element`` handles for all matches.

        Handles can be passed as ``scope=`` for nested ``element.find_all`` /
        ``element.find`` lookups. For human-readable strings, use
        ``Describe Element`` on each handle.

        | =Argument= | =Description= |
        | ``*locators`` | One or more locator tokens merged into a single ``find_all(...)`` call on the resolved scope. |
        | ``limit`` | Optional maximum number of returned elements. Must be ``>= 1`` when provided. |
        | ``scope`` | Optional page, frame, or parent element. When omitted, uses the active page/frame. |
        | ``timeout`` | Optional Robot timeout string (e.g. ``5s``) forwarded to Vibium ``find_all``. |

        Returns:
            list: Vibium ``Element`` handles (possibly empty).

        Raises:
            LocatorSyntaxError: If ``limit`` is provided and lower than ``1``.

        Example:
            | @{rows}=     Find Elements    css:.row
            | @{first2}=   Find Elements    role:listitem    limit=2
            | ${card}=     Find Element    css:.card
            | @{items}=    Find Elements    css:li    scope=${card}
        """
        page = self.library._session.resolve_scope(scope)
        args, kwargs = resolve_required_locators(locators)
        timeout_ms = optional_timeout_ms(timeout, library=self.library)
        if timeout_ms is not None:
            kwargs = {**kwargs, "timeout": timeout_ms}
        logger.info(f"Finding all elements '{format_locators(locators)}'.")
        elements = page.find_all(*args, **kwargs)

        if limit is not None:
            if limit < 1:
                raise LocatorSyntaxError("Find Elements: 'limit' must be >= 1.")
            elements = elements[:limit]
        return list(elements)

    @keyword("Count Elements")
    def count_elements(
        self,
        *locators: str,
        assertion_operator: AssertionOperator | None = None,
        assertion_expected: Any = None,
        message: str | None = None,
        scope: object = None,
        timeout: str | None = None,
    ) -> Any:
        """Return how many elements match the locator(s).

        Optionally asserts with AssertionEngine. Trailing ``operator`` +
        ``expected`` may be peeled from ``*locators``; named assertion kwargs
        win over peel. Expected counts from Robot (string or int) are coerced
        to ``int`` before compare (compatible with AssertionEngine 3.0.x).

        | =Argument= | =Description= |
        | ``*locators`` | One or more locator tokens merged into a single ``find_all(...)`` call. Optional trailing assertion operator + expected. |
        | ``assertion_operator`` | Optional AssertionEngine operator. |
        | ``assertion_expected`` | Expected count when asserting. |
        | ``message`` | Optional custom assertion failure message. |
        | ``scope`` | Optional page, frame, or parent element. When omitted, uses the active page/frame. |
        | ``timeout`` | Optional Robot timeout string (e.g. ``5s``) forwarded to Vibium ``find_all``. |

        Example:
            | ${count}=    Count Elements    css:.item
            | Count Elements    css:p    ==    ${2}
            | ${n}=        Count Elements    css:li    scope=${card}
        """
        targets, op, expected = split_locators_and_assertion(
            *locators,
            assertion_operator=assertion_operator,
            assertion_expected=assertion_expected,
        )
        page = self.library._session.resolve_scope(scope)
        args, kwargs = resolve_required_locators(targets)
        timeout_ms = optional_timeout_ms(timeout, library=self.library)
        if timeout_ms is not None:
            kwargs = {**kwargs, "timeout": timeout_ms}
        logger.info(f"Counting elements '{format_locators(targets)}'.")
        count = len(page.find_all(*args, **kwargs))
        if op is None:
            return count
        return assert_value(
            count, op, coerce_int(expected), "Element count", message
        )

    @keyword("Evaluate JavaScript")
    def evaluate_javascript(self, expression: str, scope: object = None):
        """Evaluate JavaScript in the resolved scope and return its result.

        | =Argument= | =Description= |
        | ``expression`` | JavaScript expression or function to execute. |
        | ``scope`` | Optional page/frame object. When omitted, uses the active scope. |

        Returns:
            Any: Deserialized value returned by the browser runtime.

        Example:
            | ${ready}=    Evaluate JavaScript    () => document.readyState
        """
        page = self.library._session.resolve_scope(scope)
        logger.info("Evaluating JavaScript expression.")
        return page.evaluate(expression)

    @keyword("Get Accessibility Tree")
    def get_accessibility_tree(
        self, everything: bool = False, scope: object = None
    ) -> str:
        """Return the accessibility tree for the resolved scope.

        | =Argument= | =Description= |
        | ``everything`` | When ``True``, requests all nodes from the accessibility tree. Default is ``False``. |
        | ``scope`` | Optional page/frame object. When omitted, uses the active scope. |

        Returns:
            str: String representation of the accessibility tree.

        Example:
            | ${tree}=    Get Accessibility Tree
            | ${full}=    Get Accessibility Tree    everything=${TRUE}
        """
        page = self.library._session.resolve_scope(scope)
        logger.info(f"Reading accessibility tree (everything={everything}).")
        return str(page.a11y_tree(everything=everything))
