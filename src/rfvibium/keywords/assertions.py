"""Read-only content and state keywords."""

from __future__ import annotations

from robot.api import logger
from robot.api.deco import keyword

from ..errors import LocatorSyntaxError
from ..locator import format_locators, resolve_element, resolve_required_locators
from ..utils import optional_timeout_ms


class AssertionKeywords:
    """Keywords to read page state."""

    def __init__(self, library):
        self.library = library

    @keyword("Get Url")
    def get_url(self, scope: object = None) -> str:
        """Return the current URL from the resolved scope.

        | =Argument= | =Description= |
        | ``scope`` | Optional page/frame object. When omitted, uses the active scope. |


                Returns:
                    str: The current URL.

                Example:
                    | ${url}=    Get Url
                    | ${url}=    Get Url    scope=${page}
                    | Should Contain    ${url}    /dashboard
        """
        page = self.library._session.resolve_scope(scope)
        return page.url()

    @keyword("Get Title")
    def get_title(self, scope: object = None) -> str:
        """Return the document title from the resolved scope.

            | =Argument= | =Description= |
            | ``scope`` | Optional page/frame object. When omitted, uses the active scope. |

            Returns:
        str: The page title. The underlying Vibium client may return an empty

                string when no title is available.

            Example:
                | ${title}=    Get Title
                | ${title}=    Get Title    scope=${page}
        """
        page = self.library._session.resolve_scope(scope)
        return page.title()

    @keyword("Get Page Text")
    def get_page_text(self, scope: object = None) -> str:
        """Return visible text from ``document.body.innerText`` in the resolved scope.

        | =Argument= | =Description= |
        | ``scope`` | Optional page/frame object. When omitted, uses the active scope. |


                Returns:
                    str: Visible text content of the body element, or an empty string when
                    body is missing.

                Example:
                    | ${text}=    Get Page Text
                    | ${frame_text}=    Get Page Text    scope=${frame}
        """
        page = self.library._session.resolve_scope(scope)
        return page.evaluate("document.body ? document.body.innerText : ''")

    @keyword("Get Html")
    def get_html(
        self, *locators, outer: bool = True, scope: object = None, timeout: str | None = None
    ) -> str:
        """Return HTML from the resolved scope or a resolved element.

            | =Argument= | =Description= |
            | ``*locators`` | Optional. Element HTML: locator string(s) or a single element handle. When omitted, reads page-level HTML. |
            | ``outer`` | Controls page-level output when no locators are provided. Default is ``True``. - ``True``: full document HTML via ``page.content()``. - ``False``: body inner HTML via ``document.body.innerHTML``. |
            | ``scope`` | Optional page, frame, or parent. Defaults to the active scope. Omit with an element handle. |
            | ``timeout`` | Optional Robot timeout string for locating the element (``find``). Ignored for page-level HTML. |

            Returns:
        str: HTML content.

            Raises:
        LocatorSyntaxError: When locators/handle are provided with ``outer=False``.

            Example:
                | ${doc}=    Get Html
                | ${body}=    Get Html    outer=${FALSE}
                | ${card}=    Get Html    css:.card
                | ${el}=     Find Element    css:.card
                | ${html}=   Get Html    ${el}
        """
        if not locators:
            page = self.library._session.resolve_scope(scope)
            if outer:
                return page.content()
            return page.evaluate("document.body ? document.body.innerHTML : ''")

        if not outer:
            raise LocatorSyntaxError(
                "Get Html with locators supports only outer=True for now."
            )

        timeout_ms = optional_timeout_ms(timeout)
        element = resolve_element(
            self.library._session, *locators, scope=scope, timeout=timeout_ms
        )
        logger.info(f"Reading HTML from element '{format_locators(locators)}'.")
        return element.html()

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
        timeout_ms = optional_timeout_ms(timeout)
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
        self, *locators: str, scope: object = None, timeout: str | None = None
    ) -> int:
        """Return how many elements match the locator(s).

            | =Argument= | =Description= |
            | ``*locators`` | One or more locator tokens merged into a single ``find_all(...)`` call on the resolved scope. |
            | ``scope`` | Optional page, frame, or parent element. When omitted, uses the active page/frame. |
            | ``timeout`` | Optional Robot timeout string (e.g. ``5s``) forwarded to Vibium ``find_all``. |

            Returns:
        int: Number of matched elements.

            Example:
                | ${count}=    Count Elements    css:.item
                | ${n}=        Count Elements    css:li    scope=${card}
        """
        page = self.library._session.resolve_scope(scope)
        args, kwargs = resolve_required_locators(locators)
        timeout_ms = optional_timeout_ms(timeout)
        if timeout_ms is not None:
            kwargs = {**kwargs, "timeout": timeout_ms}
        logger.info(f"Counting elements '{format_locators(locators)}'.")
        return len(page.find_all(*args, **kwargs))

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
