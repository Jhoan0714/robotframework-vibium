"""Interaction keywords aligned to Vibium's ``Page.find`` + ``Element`` API.

Public contract:

- ``Click`` / ``Find Element`` accept one or more locator tokens;
  each token uses ``strategy:value`` syntax or a plain CSS selector. Tokens
  are merged into a single ``page.find(...)`` / ``scope.find(...)`` call.
  ``Find Element`` returns a Vibium ``Element`` handle (usable as ``scope=``
  for nested find). Use ``Describe Element`` for a human-readable ``repr``.
  Action and getter keywords accept a sole element handle as the target
  (no second ``find``), in addition to locator tokens.
- ``Fill Text`` additionally accepts a value. Two usage modes:
    1. Ergonomic (value as last positional).
    2. Explicit (``value=...`` as Robot Framework keyword argument).
  The ergonomic mode is refused when the last positional looks like a locator
  (starts with a known ``strategy:`` prefix); the user must then use
  ``value=...`` to disambiguate.
- ``Upload Files`` resolves ``*locators`` like other interaction keywords and
  requires file paths via the keyword-only argument ``files=`` (a string or a
  list/tuple of strings).
- ``Drag And Drop`` resolves a **source** element and a **target** element
  (each as one locator token or a list/tuple of tokens) and calls
  ``source.drag_to(target)``.
"""

from __future__ import annotations

import json
from typing import Any, Optional

from assertionengine import AssertionOperator
from robot.api import logger
from robot.api.deco import keyword

from ..assertions.helper import (
    assert_list,
    assert_value,
    split_locators_and_assertion,
)
from ..errors import LocatorSyntaxError
from ..locators.locator import (
    format_locators,
    looks_like_locator,
    merge_locators,
    resolve_element,
    resolve_required_locators,
)
from ..types import UNSET, Element, FindScope, Locator, PageScope
from ..utils import optional_timeout_ms


class InteractionKeywords:
    """Keywords for user-like interactions."""

    def __init__(self, library):
        self.library = library

    @keyword("Map Elements", tags=["Page", "Getter"])
    def map_elements(self, scope: PageScope = None) -> str:
        """Return accessibility tree information for the resolved scope.

        | =Argument= | =Description= |
        | ``scope`` | Optional page/frame object. When omitted, uses the active scope. |

        Returns:
            Accessibility tree as a string.

        Example:
            | ${tree}=    Map Elements
            | ${tree}=    Map Elements    scope=${frame}
        """
        page = self.library._session.resolve_scope(scope)
        return str(page.a11y_tree())

    @keyword("Click", tags=["Element", "Action"])
    def click(
        self, *locators: Locator, scope: FindScope = None, timeout: Optional[str] = None
    ) -> None:
        """Click an element resolved from locator token(s) or an element handle.

        | =Argument= | =Description= |
        | ``*locators`` | Element to act on: locator string(s) or a single element handle. |
        | ``scope`` | Optional page, frame, or parent. Defaults to the active scope. Omit with an element handle. |
        | ``timeout`` | Optional Robot timeout string (e.g. ``5s``). Forwarded to Vibium ``find`` when resolving locators and to the element action. With a sole element handle, only the action uses it. |

        Example:
            | Click    role:button    text:Log in
            | Click    css:.submit
            | ${btn}=    Find Element    css:#save
            | Click    ${btn}
            | Click    css:button    scope=${card}
        """
        timeout_ms = optional_timeout_ms(timeout, library=self.library)
        element = resolve_element(
            self.library._session, *locators, scope=scope, timeout=timeout_ms
        )
        logger.info(f"Clicking element '{format_locators(locators)}'.")
        element.click(timeout=timeout_ms)

    @keyword("Find Element", tags=["Element", "Getter"])
    def find_element(
        self, *locators: Locator, scope: FindScope = None, timeout: Optional[str] = None
    ) -> Element:
        """Resolve locator token(s) and return a Vibium ``Element`` handle.

        The handle can be passed as ``scope=`` to interaction/getter keywords
        (and to ``Find Element`` / ``Find Elements``) for nested
        ``element.find(...)`` lookups, or as the sole ``*locators`` target
        on action/getter keywords. For a human-readable string, use
        ``Describe Element``.

        | =Argument= | =Description= |
        | ``*locators`` | Locator tokens merged into one ``find(...)`` call on the resolved scope. |
        | ``scope`` | Optional page, frame, or parent element. When omitted, uses the active page/frame. |
        | ``timeout`` | Optional Robot timeout string (e.g. ``5s``) forwarded to Vibium ``find``. |

        Returns:
            Element handle for the first match.

        Example:
            | ${el}=      Find Element    role:textbox    label:E-mail
            | ${card}=    Find Element    css:.card
            | ${btn}=     Find Element    css:button    scope=${card}
            | ${fast}=    Find Element    css:#x    timeout=500ms
            | Click    ${btn}
            | Click    css:button    scope=${card}
        """
        page = self.library._session.resolve_scope(scope)
        args, kwargs = resolve_required_locators(locators)
        timeout_ms = optional_timeout_ms(timeout, library=self.library)
        if timeout_ms is not None:
            kwargs = {**kwargs, "timeout": timeout_ms}
        logger.info(f"Finding element '{format_locators(locators)}'.")
        return page.find(*args, **kwargs)

    @keyword("Describe Element", tags=["Element", "Getter"])
    def describe_element(self, element: Element) -> str:
        """Return a human-readable ``repr`` for an element handle.

        Use after ``Find Element`` / ``Find Elements`` when you need a string
        for logging or text assertions. Does not call the browser.

        | =Argument= | =Description= |
        | ``element`` | Element handle returned by ``Find Element`` (or an item from ``Find Elements``). |

        Returns:
            ``repr(element)`` (typically ``Element(tag='...', text='...')``).

        Example:
            | ${el}=      Find Element    css:button
            | ${desc}=    Describe Element    ${el}
            | Should Contain    ${desc}    button
        """
        return repr(element)

    @keyword("Get Text", tags=["Element", "Getter"])
    def get_text(
        self,
        *locators: Locator,
        assertion_operator: Optional[AssertionOperator] = None,
        assertion_expected: Any = None,
        message: Optional[str] = None,
        scope: FindScope = None,
        timeout: Optional[str] = None,
    ) -> Any:
        """Return ``element.text()`` for a matched element or element handle.

        Optionally asserts with AssertionEngine. Positional ``== expected`` (and
        other operators) may trail locator tokens; named ``assertion_operator`` /
        ``assertion_expected`` win over peel. ``scope`` / ``timeout`` / ``message``
        must be named.

        | =Argument= | =Description= |
        | ``*locators`` | Element to act on: locator string(s) or a single element handle. Optional trailing assertion operator + expected. |
        | ``assertion_operator`` | Optional AssertionEngine operator (e.g. ``==``, ``contains``). |
        | ``assertion_expected`` | Expected value when asserting. |
        | ``message`` | Optional custom assertion failure message. |
        | ``scope`` | Optional page, frame, or parent. Defaults to the active scope. Omit with an element handle. |
        | ``timeout`` | Optional Robot timeout string (e.g. ``5s``) forwarded to Vibium ``find`` when resolving locators. Has no effect when the target is a sole element handle. |

        Returns:
            Element text, or the [#Assertions|AssertionEngine] result when asserting.

        Example:
            | ${text}=    Get Text    css:h1
            | Get Text    css:h1    ==    Welcome
            | ${btn}=     Find Element    css:button
            | ${text}=    Get Text    ${btn}
        """
        targets, op, expected = split_locators_and_assertion(
            *locators,
            assertion_operator=assertion_operator,
            assertion_expected=assertion_expected,
        )
        timeout_ms = optional_timeout_ms(timeout, library=self.library)
        element = resolve_element(
            self.library._session, *targets, scope=scope, timeout=timeout_ms
        )
        logger.info(f"Reading text from element '{format_locators(targets)}'.")
        return assert_value(element.text(), op, expected, "Text", message)

    @keyword("Get Inner Text", tags=["Element", "Getter"])
    def get_inner_text(
        self,
        *locators: Locator,
        assertion_operator: Optional[AssertionOperator] = None,
        assertion_expected: Any = None,
        message: Optional[str] = None,
        scope: FindScope = None,
        timeout: Optional[str] = None,
    ) -> Any:
        """Return ``element.inner_text()`` for the matched element.

        Optionally asserts with AssertionEngine (same peel / kwargs rules as
        ``Get Text``).

        | =Argument= | =Description= |
        | ``*locators`` | Element to act on: locator string(s) or a single element handle. Optional trailing assertion operator + expected. |
        | ``assertion_operator`` | Optional AssertionEngine operator. |
        | ``assertion_expected`` | Expected value when asserting. |
        | ``message`` | Optional custom assertion failure message. |
        | ``scope`` | Optional page, frame, or parent. Defaults to the active scope. Omit with an element handle. |
        | ``timeout`` | Optional Robot timeout string (e.g. ``5s``) forwarded to Vibium ``find`` when resolving locators. Has no effect when the target is a sole element handle. |

        Returns:
            Inner text, or the [#Assertions|AssertionEngine] result when asserting.

        Example:
            | ${text}=    Get Inner Text    css:div.content
            | Get Inner Text    css:div.content    ==    Hello
        """
        targets, op, expected = split_locators_and_assertion(
            *locators,
            assertion_operator=assertion_operator,
            assertion_expected=assertion_expected,
        )
        timeout_ms = optional_timeout_ms(timeout, library=self.library)
        element = resolve_element(
            self.library._session, *targets, scope=scope, timeout=timeout_ms
        )
        logger.info(f"Reading inner text from element '{format_locators(targets)}'.")
        return assert_value(element.inner_text(), op, expected, "Inner Text", message)

    @keyword("Get Value", tags=["Element", "Getter"])
    def get_value(
        self,
        *locators: Locator,
        assertion_operator: Optional[AssertionOperator] = None,
        assertion_expected: Any = None,
        message: Optional[str] = None,
        scope: FindScope = None,
        timeout: Optional[str] = None,
    ) -> Any:
        """Return ``element.value()`` for the matched element.

        Optionally asserts with AssertionEngine (same peel / kwargs rules as
        ``Get Text``).

        | =Argument= | =Description= |
        | ``*locators`` | Element to act on: locator string(s) or a single element handle. Optional trailing assertion operator + expected. |
        | ``assertion_operator`` | Optional AssertionEngine operator. |
        | ``assertion_expected`` | Expected value when asserting. |
        | ``message`` | Optional custom assertion failure message. |
        | ``scope`` | Optional page, frame, or parent. Defaults to the active scope. Omit with an element handle. |
        | ``timeout`` | Optional Robot timeout string (e.g. ``5s``) forwarded to Vibium ``find`` when resolving locators. Has no effect when the target is a sole element handle. |

        Returns:
            Form control value, or the [#Assertions|AssertionEngine] result when asserting.

        Example:
            | ${value}=    Get Value    css:#email
            | Get Value    css:#email    ==    user@example.com
        """
        targets, op, expected = split_locators_and_assertion(
            *locators,
            assertion_operator=assertion_operator,
            assertion_expected=assertion_expected,
        )
        timeout_ms = optional_timeout_ms(timeout, library=self.library)
        element = resolve_element(
            self.library._session, *targets, scope=scope, timeout=timeout_ms
        )
        logger.info(f"Reading value from element '{format_locators(targets)}'.")
        return assert_value(element.value(), op, expected, "Value", message)

    @keyword("Get Attribute", tags=["Element", "Getter"])
    def get_attribute(
        self,
        name: str,
        *locators: Locator,
        assertion_operator: Optional[AssertionOperator] = None,
        assertion_expected: Any = None,
        message: Optional[str] = None,
        scope: FindScope = None,
        timeout: Optional[str] = None,
    ) -> Any:
        """Return an attribute value from the matched element.

        Optionally asserts with AssertionEngine (same peel / kwargs rules as
        ``Get Text``). Absent attributes yield ``None``.

        | =Argument= | =Description= |
        | ``name`` | Attribute name to read. |
        | ``*locators`` | Element to act on: locator string(s) or a single element handle. Optional trailing assertion operator + expected. |
        | ``assertion_operator`` | Optional AssertionEngine operator. |
        | ``assertion_expected`` | Expected value when asserting. |
        | ``message`` | Optional custom assertion failure message. |
        | ``scope`` | Optional page, frame, or parent. Defaults to the active scope. Omit with an element handle. |
        | ``timeout`` | Optional Robot timeout string (e.g. ``5s``) forwarded to Vibium ``find`` when resolving locators. Has no effect when the target is a sole element handle. |

        Returns:
            Attribute value, ``None`` if absent, or the [#Assertions|AssertionEngine] result when asserting.

        Example:
            | ${href}=    Get Attribute    href    css:a.nav
            | Get Attribute    data-id    css:button    ==    42
        """
        targets, op, expected = split_locators_and_assertion(
            *locators,
            assertion_operator=assertion_operator,
            assertion_expected=assertion_expected,
        )
        timeout_ms = optional_timeout_ms(timeout, library=self.library)
        element = resolve_element(
            self.library._session, *targets, scope=scope, timeout=timeout_ms
        )
        logger.info(
            f"Reading attribute '{name}' from element '{format_locators(targets)}'."
        )
        return assert_value(
            element.attr(name), op, expected, f"Attribute '{name}'", message
        )

    @keyword("Get Bounds", tags=["Element", "Getter"])
    def get_bounds(
        self,
        *locators: Locator,
        assertion_operator: Optional[AssertionOperator] = None,
        assertion_expected: Any = None,
        message: Optional[str] = None,
        scope: FindScope = None,
        timeout: Optional[str] = None,
    ) -> Any:
        """Return ``element.bounds()`` for the matched element.

        Optionally asserts with AssertionEngine (same peel / kwargs rules as
        ``Get Text``).

        | =Argument= | =Description= |
        | ``*locators`` | Element to act on: locator string(s) or a single element handle. Optional trailing assertion operator + expected. |
        | ``assertion_operator`` | Optional AssertionEngine operator. |
        | ``assertion_expected`` | Expected value when asserting. |
        | ``message`` | Optional custom assertion failure message. |
        | ``scope`` | Optional page, frame, or parent. Defaults to the active scope. Omit with an element handle. |
        | ``timeout`` | Optional Robot timeout string (e.g. ``5s``) forwarded to Vibium ``find`` when resolving locators. Has no effect when the target is a sole element handle. |

        Returns:
            Bounding box data, or the [#Assertions|AssertionEngine] result when asserting.

        Example:
            | ${box}=    Get Bounds    css:#banner
        """
        targets, op, expected = split_locators_and_assertion(
            *locators,
            assertion_operator=assertion_operator,
            assertion_expected=assertion_expected,
        )
        timeout_ms = optional_timeout_ms(timeout, library=self.library)
        element = resolve_element(
            self.library._session, *targets, scope=scope, timeout=timeout_ms
        )
        logger.info(f"Reading bounds from element '{format_locators(targets)}'.")
        return assert_value(element.bounds(), op, expected, "Bounds", message)

    @keyword("Element Is Visible", tags=["Element", "Getter"])
    def element_is_visible(
        self, *locators: Locator, scope: FindScope = None, timeout: Optional[str] = None
    ) -> bool:
        """Check whether the matched element is visible.

        | =Argument= | =Description= |
        | ``*locators`` | Element to act on: locator string(s) or a single element handle. |
        | ``scope`` | Optional page, frame, or parent. Defaults to the active scope. Omit with an element handle. |
        | ``timeout`` | Optional Robot timeout string (e.g. ``5s``) forwarded to Vibium ``find`` when resolving locators. Has no effect when the target is a sole element handle. |

        Returns:
            ``True`` if the element is visible, otherwise ``False``.

        Example:
            | ${ok}=    Element Is Visible    css:.modal
            | Should Be True    ${ok}
        """
        timeout_ms = optional_timeout_ms(timeout, library=self.library)
        element = resolve_element(
            self.library._session, *locators, scope=scope, timeout=timeout_ms
        )
        logger.info(f"Checking visibility of element '{format_locators(locators)}'.")
        return element.is_visible()

    @keyword("Element Is Hidden", tags=["Element", "Getter"])
    def element_is_hidden(
        self, *locators: Locator, scope: FindScope = None, timeout: Optional[str] = None
    ) -> bool:
        """Check whether the matched element is hidden.

        | =Argument= | =Description= |
        | ``*locators`` | Element to act on: locator string(s) or a single element handle. |
        | ``scope`` | Optional page, frame, or parent. Defaults to the active scope. Omit with an element handle. |
        | ``timeout`` | Optional Robot timeout string (e.g. ``5s``) forwarded to Vibium ``find`` when resolving locators. Has no effect when the target is a sole element handle. |

        Returns:
            ``True`` if the element is hidden, otherwise ``False``.

        Example:
            | ${ok}=    Element Is Hidden    css:.spinner
            | Should Be True    ${ok}
        """
        timeout_ms = optional_timeout_ms(timeout, library=self.library)
        element = resolve_element(
            self.library._session, *locators, scope=scope, timeout=timeout_ms
        )
        logger.info(f"Checking hidden state of element '{format_locators(locators)}'.")
        return element.is_hidden()

    @keyword("Element Is Enabled", tags=["Element", "Getter"])
    def element_is_enabled(
        self, *locators: Locator, scope: FindScope = None, timeout: Optional[str] = None
    ) -> bool:
        """Check whether the matched element is enabled.

        | =Argument= | =Description= |
        | ``*locators`` | Element to act on: locator string(s) or a single element handle. |
        | ``scope`` | Optional page, frame, or parent. Defaults to the active scope. Omit with an element handle. |
        | ``timeout`` | Optional Robot timeout string (e.g. ``5s``) forwarded to Vibium ``find`` when resolving locators. Has no effect when the target is a sole element handle. |

        Returns:
            ``True`` if the element is enabled, otherwise ``False``.

        Example:
            | ${ok}=    Element Is Enabled    css:button[type=submit]
            | Should Be True    ${ok}
        """
        timeout_ms = optional_timeout_ms(timeout, library=self.library)
        element = resolve_element(
            self.library._session, *locators, scope=scope, timeout=timeout_ms
        )
        logger.info(f"Checking enabled state of element '{format_locators(locators)}'.")
        return element.is_enabled()

    @keyword("Element Is Checked", tags=["Element", "Getter"])
    def element_is_checked(
        self, *locators: Locator, scope: FindScope = None, timeout: Optional[str] = None
    ) -> bool:
        """Check whether the matched element is checked.

        | =Argument= | =Description= |
        | ``*locators`` | Element to act on: locator string(s) or a single element handle. |
        | ``scope`` | Optional page, frame, or parent. Defaults to the active scope. Omit with an element handle. |
        | ``timeout`` | Optional Robot timeout string (e.g. ``5s``) forwarded to Vibium ``find`` when resolving locators. Has no effect when the target is a sole element handle. |

        Returns:
            ``True`` if the element is checked, otherwise ``False``.

        Example:
            | ${ok}=    Element Is Checked    css:#agree
            | Should Be True    ${ok}
        """
        timeout_ms = optional_timeout_ms(timeout, library=self.library)
        element = resolve_element(
            self.library._session, *locators, scope=scope, timeout=timeout_ms
        )
        logger.info(f"Checking checked state of element '{format_locators(locators)}'.")
        return element.is_checked()

    @keyword("Element Is Editable", tags=["Element", "Getter"])
    def element_is_editable(
        self, *locators: Locator, scope: FindScope = None, timeout: Optional[str] = None
    ) -> bool:
        """Check whether the matched element is editable.

        | =Argument= | =Description= |
        | ``*locators`` | Element to act on: locator string(s) or a single element handle. |
        | ``scope`` | Optional page, frame, or parent. Defaults to the active scope. Omit with an element handle. |
        | ``timeout`` | Optional Robot timeout string (e.g. ``5s``) forwarded to Vibium ``find`` when resolving locators. Has no effect when the target is a sole element handle. |

        Returns:
            ``True`` if the element is editable, otherwise ``False``.

        Example:
            | ${ok}=    Element Is Editable    css:#name
            | Should Be True    ${ok}
        """
        timeout_ms = optional_timeout_ms(timeout, library=self.library)
        element = resolve_element(
            self.library._session, *locators, scope=scope, timeout=timeout_ms
        )
        logger.info(
            f"Checking editable state of element '{format_locators(locators)}'."
        )
        return element.is_editable()

    @keyword("Get Role", tags=["Element", "Getter"])
    def get_role(
        self,
        *locators: Locator,
        assertion_operator: Optional[AssertionOperator] = None,
        assertion_expected: Any = None,
        message: Optional[str] = None,
        scope: FindScope = None,
        timeout: Optional[str] = None,
    ) -> Any:
        """Return semantic role for the matched element.

        Optionally asserts with AssertionEngine (same peel / kwargs rules as
        ``Get Text``).

        | =Argument= | =Description= |
        | ``*locators`` | Element to act on: locator string(s) or a single element handle. Optional trailing assertion operator + expected. |
        | ``assertion_operator`` | Optional AssertionEngine operator. |
        | ``assertion_expected`` | Expected value when asserting. |
        | ``message`` | Optional custom assertion failure message. |
        | ``scope`` | Optional page, frame, or parent. Defaults to the active scope. Omit with an element handle. |
        | ``timeout`` | Optional Robot timeout string (e.g. ``5s``) forwarded to Vibium ``find`` when resolving locators. Has no effect when the target is a sole element handle. |

        Returns:
            Semantic role, or the [#Assertions|AssertionEngine] result when asserting.

        Example:
            | ${role}=    Get Role    css:button
            | Get Role    css:button    ==    button
        """
        targets, op, expected = split_locators_and_assertion(
            *locators,
            assertion_operator=assertion_operator,
            assertion_expected=assertion_expected,
        )
        timeout_ms = optional_timeout_ms(timeout, library=self.library)
        element = resolve_element(
            self.library._session, *targets, scope=scope, timeout=timeout_ms
        )
        logger.info(f"Reading role of element '{format_locators(targets)}'.")
        return assert_value(element.role(), op, expected, "Role", message)

    @keyword("Get Label", tags=["Element", "Getter"])
    def get_label(
        self,
        *locators: Locator,
        assertion_operator: Optional[AssertionOperator] = None,
        assertion_expected: Any = None,
        message: Optional[str] = None,
        scope: FindScope = None,
        timeout: Optional[str] = None,
    ) -> Any:
        """Return accessible label for the matched element.

        Optionally asserts with AssertionEngine (same peel / kwargs rules as
        ``Get Text``).

        | =Argument= | =Description= |
        | ``*locators`` | Element to act on: locator string(s) or a single element handle. Optional trailing assertion operator + expected. |
        | ``assertion_operator`` | Optional AssertionEngine operator. |
        | ``assertion_expected`` | Expected value when asserting. |
        | ``message`` | Optional custom assertion failure message. |
        | ``scope`` | Optional page, frame, or parent. Defaults to the active scope. Omit with an element handle. |
        | ``timeout`` | Optional Robot timeout string (e.g. ``5s``) forwarded to Vibium ``find`` when resolving locators. Has no effect when the target is a sole element handle. |

        Returns:
            Accessible label, or the [#Assertions|AssertionEngine] result when asserting.

        Example:
            | ${label}=    Get Label    css:#email
            | Get Label    css:#email    ==    E-mail
        """
        targets, op, expected = split_locators_and_assertion(
            *locators,
            assertion_operator=assertion_operator,
            assertion_expected=assertion_expected,
        )
        timeout_ms = optional_timeout_ms(timeout, library=self.library)
        element = resolve_element(
            self.library._session, *targets, scope=scope, timeout=timeout_ms
        )
        logger.info(f"Reading label of element '{format_locators(targets)}'.")
        return assert_value(element.label(), op, expected, "Label", message)

    @keyword("Get Element States", tags=["Element", "Getter"])
    def get_element_states(
        self,
        *locators: Locator,
        assertion_operator: Optional[AssertionOperator] = None,
        assertion_expected: Any = None,
        message: Optional[str] = None,
        scope: FindScope = None,
        timeout: Optional[str] = None,
    ) -> Any:
        """Return active states for the matched element as a list of names.

        States are derived from the same Vibium checks as ``Element Is Visible``,
        ``Element Is Hidden``, ``Element Is Enabled``, ``Element Is Checked``, and
        ``Element Is Editable``. Those keywords remain available; this getter is
        additive.

        Optionally asserts with AssertionEngine (same peel / kwargs rules as
        ``Get Text``). For list operators such as ``contains`` / ``*=``, the
        expected value may be a single state name or a list.

        | =Argument= | =Description= |
        | ``*locators`` | Element to act on: locator string(s) or a single element handle. Optional trailing assertion operator + expected. |
        | ``assertion_operator`` | Optional AssertionEngine operator. |
        | ``assertion_expected`` | Expected state name or list of names. |
        | ``message`` | Optional custom assertion failure message. |
        | ``scope`` | Optional page, frame, or parent. Defaults to the active scope. Omit with an element handle. |
        | ``timeout`` | Optional Robot timeout string (e.g. ``5s``) forwarded to Vibium ``find``. |

        Returns:
            Active state names (e.g. ``visible``, ``enabled``), or the
            [#Assertions|AssertionEngine] result when asserting.

        Example:
            | @{states}=    Get Element States    css:button
            | Get Element States    css:button    *=    visible
        """
        targets, op, expected = split_locators_and_assertion(
            *locators,
            assertion_operator=assertion_operator,
            assertion_expected=assertion_expected,
        )
        timeout_ms = optional_timeout_ms(timeout, library=self.library)
        element = resolve_element(
            self.library._session, *targets, scope=scope, timeout=timeout_ms
        )
        logger.info(f"Reading states of element '{format_locators(targets)}'.")
        states: list[str] = []
        if element.is_visible():
            states.append("visible")
        if element.is_hidden():
            states.append("hidden")
        if element.is_enabled():
            states.append("enabled")
        try:
            if element.is_checked():
                states.append("checked")
        except Exception:
            # Vibium raises when the element is not a checkbox/radio.
            pass
        try:
            if element.is_editable():
                states.append("editable")
        except Exception:
            pass
        return assert_list(states, op, expected, "Element states", message)

    @keyword("Fill Text", tags=["Element", "Action"])
    def fill_text(
        self,
        *locators: Locator,
        value: Optional[str] = UNSET,  # type: ignore[assignment]
        secret: bool = False,
        scope: FindScope = None,
        timeout: Optional[str] = None,
    ) -> None:
        """Fill the matched element, replacing existing content.

        | =Argument= | =Description= |
        | ``*locators`` | Element to act on: locator string(s) or a single element handle. |
        | ``value`` | Explicit value to type. When provided, all positional arguments are treated as locators. |
        | ``secret`` | When ``True``, masks typed value in logs as ``***``. Default is ``False``. |
        | ``scope`` | Optional page, frame, or parent. Defaults to the active scope. Omit with an element handle. |
        | ``timeout`` | Optional Robot timeout string (e.g. ``5s``). Forwarded to Vibium ``find`` when resolving locators and to the element action. With a sole element handle, only the action uses it. |

        Note:
            The ergonomic form requires at least one locator and one trailing value.
            If the trailing value looks like a locator token, pass it with ``value=``.

        Example:
            | Fill Text    role:textbox    label:E-mail    user@example.com
            | Fill Text    role:textbox    label:Password    value=s3cret    secret=${TRUE}
        """
        locator_tokens, final_value = self._resolve_fill_arguments(locators, value)
        timeout_ms = optional_timeout_ms(timeout, library=self.library)
        element = resolve_element(
            self.library._session, *locator_tokens, scope=scope, timeout=timeout_ms
        )
        display_value = "***" if secret else repr(final_value)
        logger.info(
            f"Typing text {display_value} into element "
            f"'{format_locators(locator_tokens)}'."
        )
        element.fill(final_value, timeout=timeout_ms)

    @keyword("Press Keys", tags=["Element", "Action"])
    def press_keys(
        self,
        key: str,
        *locators: Locator,
        scope: FindScope = None,
        timeout: Optional[str] = None,
    ) -> None:
        """Press a key or combo on the matched element.

        Page-level keystrokes (no locator) use ``Keyboard Key    press``.

        | =Argument= | =Description= |
        | ``key`` | Keyboard key or combo supported by Vibium (for example ``Enter``, ``Control+a``). |
        | ``*locators`` | Element to act on: locator string(s) or a single element handle. |
        | ``scope`` | Optional page, frame, or parent. Defaults to the active scope. Omit with an element handle. |
        | ``timeout`` | Optional Robot timeout string (e.g. ``5s``). Forwarded to Vibium ``find`` when resolving locators and to the element action. With a sole element handle, only the action uses it. |

        Example:
            | Press Keys    Enter    role:textbox    label:Search
            | Press Keys    Control+a    css:#editor
        """
        timeout_ms = optional_timeout_ms(timeout, library=self.library)
        element = resolve_element(
            self.library._session, *locators, scope=scope, timeout=timeout_ms
        )
        logger.info(f"Pressing key '{key}' on element '{format_locators(locators)}'.")
        element.press(key, timeout=timeout_ms)

    @keyword("Double Click", tags=["Element", "Action"])
    def double_click(
        self, *locators: Locator, scope: FindScope = None, timeout: Optional[str] = None
    ) -> None:
        """Double-click the matched element.

        | =Argument= | =Description= |
        | ``*locators`` | Element to act on: locator string(s) or a single element handle. |
        | ``scope`` | Optional page, frame, or parent. Defaults to the active scope. Omit with an element handle. |
        | ``timeout`` | Optional Robot timeout string (e.g. ``5s``). Forwarded to Vibium ``find`` when resolving locators and to the element action. With a sole element handle, only the action uses it. |

        Example:
            | Double Click    css:tr.row
            | ${el}=    Find Element    css:tr.row
            | Double Click    ${el}
        """
        timeout_ms = optional_timeout_ms(timeout, library=self.library)
        element = resolve_element(
            self.library._session, *locators, scope=scope, timeout=timeout_ms
        )
        logger.info(f"Double-clicking element '{format_locators(locators)}'.")
        element.dblclick(timeout=timeout_ms)

    @keyword("Hover", tags=["Element", "Action"])
    def hover(
        self, *locators: Locator, scope: FindScope = None, timeout: Optional[str] = None
    ) -> None:
        """Hover the mouse pointer over the matched element.

        | =Argument= | =Description= |
        | ``*locators`` | Element to act on: locator string(s) or a single element handle. |
        | ``scope`` | Optional page, frame, or parent. Defaults to the active scope. Omit with an element handle. |
        | ``timeout`` | Optional Robot timeout string (e.g. ``5s``). Forwarded to Vibium ``find`` when resolving locators and to the element action. With a sole element handle, only the action uses it. |

        Example:
            | Hover    css:.menu-item
            | ${el}=    Find Element    css:.menu-item
            | Hover    ${el}
        """
        timeout_ms = optional_timeout_ms(timeout, library=self.library)
        element = resolve_element(
            self.library._session, *locators, scope=scope, timeout=timeout_ms
        )
        logger.info(f"Hovering element '{format_locators(locators)}'.")
        element.hover(timeout=timeout_ms)

    @keyword("Tap", tags=["Element", "Action"])
    def tap(
        self, *locators: Locator, scope: FindScope = None, timeout: Optional[str] = None
    ) -> None:
        """Tap the matched element (touch input; distinct from ``Click``).

        | =Argument= | =Description= |
        | ``*locators`` | Element to act on: locator string(s) or a single element handle. |
        | ``scope`` | Optional page, frame, or parent. Defaults to the active scope. Omit with an element handle. |
        | ``timeout`` | Optional Robot timeout string (e.g. ``5s``). Forwarded to Vibium ``find`` when resolving locators and to the element action. With a sole element handle, only the action uses it. |

        Example:
            | Tap    css:#btn
            | ${el}=    Find Element    css:#btn
            | Tap    ${el}
        """
        timeout_ms = optional_timeout_ms(timeout, library=self.library)
        element = resolve_element(
            self.library._session, *locators, scope=scope, timeout=timeout_ms
        )
        logger.info(f"Tapping element '{format_locators(locators)}'.")
        element.tap(timeout=timeout_ms)

    @keyword("Highlight", tags=["Element", "Action"])
    def highlight(
        self, *locators: Locator, scope: FindScope = None, timeout: Optional[str] = None
    ) -> None:
        """Briefly outline the matched element so a watcher can see it.

        | =Argument= | =Description= |
        | ``*locators`` | Element to act on: locator string(s) or a single element handle. |
        | ``scope`` | Optional page, frame, or parent. Defaults to the active scope. Omit with an element handle. |
        | ``timeout`` | Optional Robot timeout string (e.g. ``5s``). Forwarded to Vibium ``find`` when resolving locators and to the element action. With a sole element handle, only the action uses it. |

        Example:
            | Highlight    css:.error
            | ${el}=    Find Element    css:.error
            | Highlight    ${el}
        """
        timeout_ms = optional_timeout_ms(timeout, library=self.library)
        element = resolve_element(
            self.library._session, *locators, scope=scope, timeout=timeout_ms
        )
        logger.info(f"Highlighting element '{format_locators(locators)}'.")
        element.highlight(timeout=timeout_ms)

    @keyword("Focus", tags=["Element", "Action"])
    def focus(
        self, *locators: Locator, scope: FindScope = None, timeout: Optional[str] = None
    ) -> None:
        """Set focus on the matched element.

        | =Argument= | =Description= |
        | ``*locators`` | Element to act on: locator string(s) or a single element handle. |
        | ``scope`` | Optional page, frame, or parent. Defaults to the active scope. Omit with an element handle. |
        | ``timeout`` | Optional Robot timeout string (e.g. ``5s``). Forwarded to Vibium ``find`` when resolving locators and to the element action. With a sole element handle, only the action uses it. |

        Example:
            | Focus    css:#search
            | ${el}=    Find Element    css:#search
            | Focus    ${el}
        """
        timeout_ms = optional_timeout_ms(timeout, library=self.library)
        element = resolve_element(
            self.library._session, *locators, scope=scope, timeout=timeout_ms
        )
        logger.info(f"Focusing element '{format_locators(locators)}'.")
        element.focus(timeout=timeout_ms)

    @keyword("Clear Text", tags=["Element", "Action"])
    def clear_text(
        self, *locators: Locator, scope: FindScope = None, timeout: Optional[str] = None
    ) -> None:
        """Clear the value of the matched element.

        | =Argument= | =Description= |
        | ``*locators`` | Element to act on: locator string(s) or a single element handle. |
        | ``scope`` | Optional page, frame, or parent. Defaults to the active scope. Omit with an element handle. |
        | ``timeout`` | Optional Robot timeout string (e.g. ``5s``). Forwarded to Vibium ``find`` when resolving locators and to the element action. With a sole element handle, only the action uses it. |

        Example:
            | Clear Text    css:#email
            | ${el}=    Find Element    css:#email
            | Clear Text    ${el}
        """
        timeout_ms = optional_timeout_ms(timeout, library=self.library)
        element = resolve_element(
            self.library._session, *locators, scope=scope, timeout=timeout_ms
        )
        logger.info(f"Clearing element '{format_locators(locators)}'.")
        element.clear(timeout=timeout_ms)

    @keyword("Type Text", tags=["Element", "Action"])
    def type_text(
        self,
        *locators: Locator,
        text: Optional[str] = UNSET,  # type: ignore[assignment]
        secret: bool = False,
        scope: FindScope = None,
        timeout: Optional[str] = None,
    ) -> None:
        """Type text into the matched element in append mode.

        | =Argument= | =Description= |
        | ``*locators`` | Element to act on: locator string(s) or a single element handle. |
        | ``text`` | Explicit text to type. When provided, all positional arguments are treated as locators. |
        | ``secret`` | When ``True``, masks typed text in logs as ``***``. Default is ``False``. |
        | ``scope`` | Optional page, frame, or parent. Defaults to the active scope. Omit with an element handle. |
        | ``timeout`` | Optional Robot timeout string (e.g. ``5s``). Forwarded to Vibium ``find`` when resolving locators and to the element action. With a sole element handle, only the action uses it. |

        Example:
            | Type Text    css:#notes    more text
            | Type Text    css:#notes    text=more text
        """
        locator_tokens, final_text = self._resolve_tail_value_arguments(
            keyword_name="Type Text",
            positional=locators,
            explicit=text,
            explicit_name="text",
        )
        timeout_ms = optional_timeout_ms(timeout, library=self.library)
        element = resolve_element(
            self.library._session, *locator_tokens, scope=scope, timeout=timeout_ms
        )
        display_value = "***" if secret else repr(final_text)
        logger.info(
            f"Typing text {display_value} into element "
            f"'{format_locators(locator_tokens)}' (append mode)."
        )
        element.type(final_text, timeout=timeout_ms)

    @keyword("Select Option", tags=["Element", "Action"])
    def select_option(
        self,
        *locators: Locator,
        value: Optional[str] = UNSET,  # type: ignore[assignment]
        scope: FindScope = None,
        timeout: Optional[str] = None,
    ) -> None:
        """Select an option value in a matched ``<select>`` element.

        | =Argument= | =Description= |
        | ``*locators`` | Element to act on: locator string(s) or a single element handle. |
        | ``value`` | Explicit option value to select. |
        | ``scope`` | Optional page, frame, or parent. Defaults to the active scope. Omit with an element handle. |
        | ``timeout`` | Optional Robot timeout string (e.g. ``5s``). Forwarded to Vibium ``find`` when resolving locators and to the element action. With a sole element handle, only the action uses it. |

        Example:
            | Select Option    css:#country    us
            | Select Option    css:#country    value=us
        """
        locator_tokens, option_value = self._resolve_tail_value_arguments(
            keyword_name="Select Option",
            positional=locators,
            explicit=value,
            explicit_name="value",
        )
        timeout_ms = optional_timeout_ms(timeout, library=self.library)
        element = resolve_element(
            self.library._session, *locator_tokens, scope=scope, timeout=timeout_ms
        )
        logger.info(
            f"Selecting option {repr(option_value)} in element "
            f"'{format_locators(locator_tokens)}'."
        )
        element.select_option(option_value, timeout=timeout_ms)

    @keyword("Check", tags=["Element", "Action"])
    def check(
        self, *locators: Locator, scope: FindScope = None, timeout: Optional[str] = None
    ) -> None:
        """Check a matched checkbox or radio control.

        | =Argument= | =Description= |
        | ``*locators`` | Element to act on: locator string(s) or a single element handle. |
        | ``scope`` | Optional page, frame, or parent. Defaults to the active scope. Omit with an element handle. |
        | ``timeout`` | Optional Robot timeout string (e.g. ``5s``). Forwarded to Vibium ``find`` when resolving locators and to the element action. With a sole element handle, only the action uses it. |

        Example:
            | Check    css:#agree
            | ${el}=    Find Element    css:#agree
            | Check    ${el}
        """
        timeout_ms = optional_timeout_ms(timeout, library=self.library)
        element = resolve_element(
            self.library._session, *locators, scope=scope, timeout=timeout_ms
        )
        logger.info(f"Checking element '{format_locators(locators)}'.")
        element.check(timeout=timeout_ms)

    @keyword("Uncheck", tags=["Element", "Action"])
    def uncheck(
        self, *locators: Locator, scope: FindScope = None, timeout: Optional[str] = None
    ) -> None:
        """Uncheck a matched checkbox control.

        | =Argument= | =Description= |
        | ``*locators`` | Element to act on: locator string(s) or a single element handle. |
        | ``scope`` | Optional page, frame, or parent. Defaults to the active scope. Omit with an element handle. |
        | ``timeout`` | Optional Robot timeout string (e.g. ``5s``). Forwarded to Vibium ``find`` when resolving locators and to the element action. With a sole element handle, only the action uses it. |

        Example:
            | Uncheck    css:#newsletter
            | ${el}=    Find Element    css:#newsletter
            | Uncheck    ${el}
        """
        timeout_ms = optional_timeout_ms(timeout, library=self.library)
        element = resolve_element(
            self.library._session, *locators, scope=scope, timeout=timeout_ms
        )
        logger.info(f"Unchecking element '{format_locators(locators)}'.")
        element.uncheck(timeout=timeout_ms)

    @keyword("Scroll Into View", tags=["Element", "Action"])
    def scroll_into_view(
        self, *locators: Locator, scope: FindScope = None, timeout: Optional[str] = None
    ) -> None:
        """Scroll until the matched element is in view.

        | =Argument= | =Description= |
        | ``*locators`` | Element to act on: locator string(s) or a single element handle. |
        | ``scope`` | Optional page, frame, or parent. Defaults to the active scope. Omit with an element handle. |
        | ``timeout`` | Optional Robot timeout string (e.g. ``5s``). Forwarded to Vibium ``find`` when resolving locators and to the element action. With a sole element handle, only the action uses it. |

        Example:
            | Scroll Into View    css:#footer
            | ${el}=    Find Element    css:#footer
            | Scroll Into View    ${el}
        """
        timeout_ms = optional_timeout_ms(timeout, library=self.library)
        element = resolve_element(
            self.library._session, *locators, scope=scope, timeout=timeout_ms
        )
        logger.info(f"Scrolling element into view '{format_locators(locators)}'.")
        element.scroll_into_view(timeout=timeout_ms)

    @keyword("Scroll", tags=["Page", "Action"])
    def scroll(
        self,
        direction: str = "down",
        amount: int = 3,
        *locators: Locator,
        scope: FindScope = None,
    ) -> None:
        """Scroll the page or a CSS container selector.

        | =Argument= | =Description= |
        | ``direction`` | Scroll direction accepted by Vibium. Default is ``down``. |
        | ``amount`` | Scroll amount/steps. Default is ``3``. |
        | ``*locators`` | Optional single CSS selector limiting scroll container. |
        | ``scope`` | Optional page/frame object. When omitted, uses the active scope. |

        Note:
            Raises ``LocatorSyntaxError`` if non-CSS locator axes are used for
            scoped scroll.

        Example:
            | Scroll
            | Scroll    up    2
            | Scroll    down    3    .panel
        """
        page = self.library._session.resolve_scope(scope)
        selector = self._resolve_scroll_selector(locators)
        if selector:
            logger.info(
                f"Scrolling direction='{direction}' amount={amount} "
                f"within selector '{selector}'."
            )
        else:
            logger.info(f"Scrolling direction='{direction}' amount={amount}.")
        page.scroll(direction=direction, amount=amount, selector=selector)

    @keyword("Dispatch Event", tags=["Element", "Action"])
    def dispatch_event(
        self,
        *locators: Locator,
        event: str,
        event_init: object = None,
        scope: FindScope = None,
        timeout: Optional[str] = None,
    ) -> None:
        """Dispatch a DOM event on the matched element.

        | =Argument= | =Description= |
        | ``*locators`` | Element to act on: locator string(s) or a single element handle. |
        | ``event`` | Event name to dispatch (for example ``click`` or ``change``). |
        | ``event_init`` | Optional event init payload as dict or JSON object string. |
        | ``scope`` | Optional page, frame, or parent. Defaults to the active scope. Omit with an element handle. |
        | ``timeout`` | Optional Robot timeout string (e.g. ``5s``). Forwarded to Vibium ``find`` when resolving locators and to the element action. With a sole element handle, only the action uses it. |

        Note:
            Raises ``LocatorSyntaxError`` if ``event_init`` is invalid JSON/object
            shape.

        Example:
            | Dispatch Event    css:#field    event=change
            | Dispatch Event    css:#field    event=custom    event_init={"detail": 1}
        """
        timeout_ms = optional_timeout_ms(timeout, library=self.library)
        element = resolve_element(
            self.library._session, *locators, scope=scope, timeout=timeout_ms
        )
        init_payload = self._coerce_event_init(event_init)
        logger.info(
            f"Dispatching event '{event}' on element '{format_locators(locators)}'."
        )
        element.dispatch_event(event, init_payload, timeout=timeout_ms)

    @keyword("Upload Files", tags=["Element", "Action"])
    def upload_files(
        self,
        *locators: Locator,
        files: object,
        scope: FindScope = None,
        timeout: Optional[str] = None,
    ) -> None:
        """Upload one or more files into a matched file input.

        | =Argument= | =Description= |
        | ``*locators`` | Element to act on: locator string(s) or a single element handle. |
        | ``files`` | File path string or list/tuple of path strings. |
        | ``scope`` | Optional page, frame, or parent. Defaults to the active scope. Omit with an element handle. |
        | ``timeout`` | Optional Robot timeout string (e.g. ``5s``). Forwarded to Vibium ``find`` when resolving locators and to the element action. With a sole element handle, only the action uses it. |

        Note:
            Raises ``LocatorSyntaxError`` if file paths are empty/invalid.

        Example:
            | Upload Files    css:input[type='file']    files=/tmp/a.pdf
            | Upload Files    css:input[type='file']    files=@{LIST}
        """
        file_paths = InteractionKeywords._coerce_upload_files(files)
        timeout_ms = optional_timeout_ms(timeout, library=self.library)
        element = resolve_element(
            self.library._session, *locators, scope=scope, timeout=timeout_ms
        )
        logger.info(
            f"Uploading {len(file_paths)} file(s) to element "
            f"'{format_locators(locators)}'."
        )
        element.set_files(file_paths, timeout=timeout_ms)

    @keyword("Drag And Drop", tags=["Element", "Action"])
    def drag_and_drop(
        self,
        source: object,
        target: object,
        timeout: Optional[str] = None,
        scope: FindScope = None,
    ) -> None:
        """Drag one resolved element to another.

        | =Argument= | =Description= |
        | ``source`` | Source locator token string or list/tuple of locator tokens. |
        | ``target`` | Target locator token string or list/tuple of locator tokens. |
        | ``timeout`` | Optional Robot timeout string (e.g. ``5s``). Forwarded to Vibium ``find`` for source/target and to ``drag_to``. |
        | ``scope`` | Optional page/frame object. When omitted, uses the active scope. |
        Note:
            Raises ``LocatorSyntaxError`` if source/target locator shapes are
            invalid.

        Example:
            | Drag And Drop    css:#src    css:#tgt
            | Drag And Drop    source=@{SRC}    target=@{TGT}    timeout=10s
        """
        page = self.library._session.resolve_scope(scope)
        src_tokens = InteractionKeywords._coerce_locator_token_group("source", source)
        tgt_tokens = InteractionKeywords._coerce_locator_token_group("target", target)
        src_args, src_kwargs = resolve_required_locators(src_tokens)
        tgt_args, tgt_kwargs = resolve_required_locators(tgt_tokens)
        timeout_ms = optional_timeout_ms(timeout, library=self.library)
        if timeout_ms is not None:
            src_kwargs = {**src_kwargs, "timeout": timeout_ms}
            tgt_kwargs = {**tgt_kwargs, "timeout": timeout_ms}

        logger.info(
            f"Dragging from '{format_locators(src_tokens)}' "
            f"to '{format_locators(tgt_tokens)}'."
        )
        source_el = page.find(*src_args, **src_kwargs)
        target_el = page.find(*tgt_args, **tgt_kwargs)
        source_el.drag_to(target_el, timeout=timeout_ms)

    @staticmethod
    def _resolve_fill_arguments(locators, value):
        return InteractionKeywords._resolve_tail_value_arguments(
            keyword_name="Fill Text",
            positional=locators,
            explicit=value,
            explicit_name="value",
        )

    @staticmethod
    def _resolve_tail_value_arguments(
        keyword_name, positional, explicit, explicit_name
    ):
        if explicit is not UNSET:
            if not positional:
                raise LocatorSyntaxError(
                    f"{keyword_name} requires at least one locator before "
                    f"'{explicit_name}='."
                )
            return tuple(positional), explicit

        if len(positional) < 2:
            raise LocatorSyntaxError(
                f"{keyword_name} requires at least one locator and a {explicit_name}. "
                f"Pass the {explicit_name} as the last argument or as "
                f"'{explicit_name}=...'."
            )

        candidate = positional[-1]
        if looks_like_locator(candidate):
            prefix = candidate.strip().split(":", 1)[0]
            raise LocatorSyntaxError(
                f"{keyword_name}: the last argument '{candidate}' looks like a "
                f"locator (prefix '{prefix}:'), not a value. "
                f"Pass the {explicit_name} explicitly with "
                f"'{explicit_name}=...' to disambiguate."
            )

        return tuple(positional[:-1]), candidate

    @staticmethod
    def _coerce_locator_token_group(side: str, value: object) -> tuple[str, ...]:
        if isinstance(value, str):
            stripped = value.strip()
            if not stripped:
                raise LocatorSyntaxError(
                    f"Drag And Drop: {side} locator cannot be an empty string."
                )
            return (stripped,)
        if isinstance(value, (list, tuple)):
            if not value:
                raise LocatorSyntaxError(
                    f"Drag And Drop: {side} must contain at least one locator token."
                )
            out: list[str] = []
            for index, item in enumerate(value):
                if not isinstance(item, str):
                    raise LocatorSyntaxError(
                        f"Drag And Drop: each {side} locator token must be a string, "
                        f"got {type(item).__name__} at index {index}."
                    )
                piece = item.strip()
                if not piece:
                    raise LocatorSyntaxError(
                        f"Drag And Drop: empty {side} locator token at index {index}."
                    )
                out.append(piece)
            return tuple(out)
        raise LocatorSyntaxError(
            f"Drag And Drop: {side} must be a string or a list/tuple of strings, "
            f"got {type(value).__name__}."
        )

    @staticmethod
    def _coerce_upload_files(files: object) -> list[str]:
        if isinstance(files, str):
            stripped = files.strip()
            if not stripped:
                raise LocatorSyntaxError(
                    "Upload Files: 'files' cannot be an empty string."
                )
            return [stripped]

        if isinstance(files, (list, tuple)):
            if not files:
                raise LocatorSyntaxError(
                    "Upload Files: 'files' cannot be an empty list."
                )
            out: list[str] = []
            for index, item in enumerate(files):
                if not isinstance(item, str):
                    raise LocatorSyntaxError(
                        "Upload Files: each entry in 'files' must be a string, "
                        f"got {type(item).__name__} at index {index}."
                    )
                piece = item.strip()
                if not piece:
                    raise LocatorSyntaxError(
                        f"Upload Files: empty string in 'files' at index {index}."
                    )
                out.append(piece)
            return out

        raise LocatorSyntaxError(
            "Upload Files: 'files' must be a string or a list/tuple of strings, "
            f"got {type(files).__name__}."
        )

    @staticmethod
    def _coerce_event_init(event_init: object) -> Any:
        if event_init is None:
            return None
        if isinstance(event_init, str):
            raw = event_init.strip()
            if not raw:
                return None
            try:
                decoded = json.loads(raw)
            except ValueError as exc:
                raise LocatorSyntaxError(
                    "Dispatch Event: 'event_init' must be valid JSON when passed "
                    f"as a string. Received: {event_init!r}"
                ) from exc
            if not isinstance(decoded, dict):
                raise LocatorSyntaxError(
                    "Dispatch Event: 'event_init' JSON must decode to an object."
                )
            return decoded
        if isinstance(event_init, dict):
            return event_init
        raise LocatorSyntaxError(
            "Dispatch Event: 'event_init' must be a dict, JSON object string, "
            "or omitted."
        )

    @staticmethod
    def _resolve_scroll_selector(locators):
        if not locators:
            return None

        args, kwargs = merge_locators(locators)
        if kwargs:
            raise LocatorSyntaxError(
                "Scroll only accepts a CSS selector when scoped "
                "(e.g. Scroll    down    3    .panel). "
                "Semantic axes like role:/xpath: are not supported by page.scroll."
            )
        if len(args) != 1:
            raise LocatorSyntaxError(
                "Scroll accepts at most one CSS selector when scoped."
            )
        return args[0]
