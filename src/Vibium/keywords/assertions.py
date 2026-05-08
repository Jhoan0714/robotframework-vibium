"""Read-only content and state keywords."""

from __future__ import annotations

from typing import Optional

from robot.api import logger
from robot.api.deco import keyword

from ..errors import LocatorSyntaxError
from ..locator import format_locators, resolve_required_locators


class AssertionKeywords:
    """Keywords to read page state."""

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
        page = self._session.resolve_scope(scope)
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
        page = self._session.resolve_scope(scope)
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
        page = self._session.resolve_scope(scope)
        return page.evaluate("document.body ? document.body.innerText : ''")

    @keyword("Get Html")
    def get_html(self, *locators: str, outer: bool = True, scope: object = None) -> str:
        """Return HTML from the resolved scope or a resolved element.

            | =Argument= | =Description= |
            | ``*locators`` | Zero or more locator tokens. When omitted, reads page-level HTML. When provided, resolves a single element with ``page.find(...)``. |
            | ``outer`` | Controls page-level output when no locators are provided. Default is ``True``. - ``True``: full document HTML via ``page.content()``. - ``False``: body inner HTML via ``document.body.innerHTML``. |
            | ``scope`` | Optional page/frame object. When omitted, uses the active scope. |

            Returns:
        str: HTML content.

            Raises:
        LocatorSyntaxError: When locators are provided with ``outer=False``.

            Example:
                | ${doc}=    Get Html
                | ${body}=    Get Html    outer=${FALSE}
                | ${card}=    Get Html    css:.card
        """
        page = self._session.resolve_scope(scope)
        if not locators:
            if outer:
                return page.content()
            return page.evaluate("document.body ? document.body.innerHTML : ''")

        if not outer:
            raise LocatorSyntaxError(
                "Get Html with locators supports only outer=True for now."
            )

        args, kwargs = resolve_required_locators(locators)
        logger.info(f"Reading HTML from element '{format_locators(locators)}'.")
        return page.find(*args, **kwargs).html()

    @keyword("Find Elements")
    def find_elements(
        self, *locators: str, limit: Optional[int] = None, scope: object = None
    ) -> list[str]:
        """Return ``repr`` strings for all elements matching the locator(s).

        | =Argument= | =Description= |
        | ``*locators`` | One or more locator tokens merged into a single ``page.find_all(...)`` call. |
        | ``limit`` | Optional maximum number of returned elements. Must be ``>= 1`` when provided. |
        | ``scope`` | Optional page/frame object. When omitted, uses the active scope. |


                Returns:
                    list[str]: Human-readable representations of matched elements.

                Raises:
                    LocatorSyntaxError: If ``limit`` is provided and lower than ``1``.

                Example:
                    | @{rows}=    Find Elements    css:.row
                    | @{first2}=    Find Elements    role:listitem    limit=2
        """
        page = self._session.resolve_scope(scope)
        args, kwargs = resolve_required_locators(locators)
        logger.info(f"Finding all elements '{format_locators(locators)}'.")
        elements = page.find_all(*args, **kwargs)

        if limit is not None:
            if limit < 1:
                raise LocatorSyntaxError("Find Elements: 'limit' must be >= 1.")
            elements = elements[:limit]
        return [repr(el) for el in elements]

    @keyword("Count Elements")
    def count_elements(self, *locators: str, scope: object = None) -> int:
        """Return how many elements match the locator(s).

            | =Argument= | =Description= |
            | ``*locators`` | One or more locator tokens merged into a single ``page.find_all(...)`` call. |
            | ``scope`` | Optional page/frame object. When omitted, uses the active scope. |

            Returns:
        int: Number of matched elements.

            Example:
                | ${count}=    Count Elements    css:.item
        """
        page = self._session.resolve_scope(scope)
        args, kwargs = resolve_required_locators(locators)
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
        page = self._session.resolve_scope(scope)
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
        page = self._session.resolve_scope(scope)
        logger.info(f"Reading accessibility tree (everything={everything}).")
        return str(page.a11y_tree(everything=everything))
